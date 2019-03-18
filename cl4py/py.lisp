(defpackage #:cl4py
  (:use #:common-lisp)
  (:export #:cl4py))

(in-package #:cl4py)

;;; Welcome to the Lisp side of cl4py. Basically, this is just a REPL that
;;; reads expressions from the Python side and prints results back to
;;; Python.

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;;
;;; Object Handles
;;;
;;; One challenge is that not all objects in Lisp can be written
;;; readably. As a pragmatic workaround, these objects are replaced by
;;; handles, by means of the #n? and #n! reader macros. The Python side is
;;; responsible for declaring when a handle may be deleted.

(defvar *handle-counter* 0)

(defvar *foreign-objects* (make-hash-table :test #'eql))

(defun free-handle (handle)
  (remhash handle *foreign-objects*))

(defun handle-object (handle)
  (or (gethash handle *foreign-objects*)
      (error "Invalid Handle.")))

(defun object-handle (object)
  (let ((handle (incf *handle-counter*)))
    (setf (gethash handle *foreign-objects*) object)
    handle))

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;;
;;; Reader Macros

(defun sharpsign-exclamation-mark (s c n)
  (declare (ignore s c))
  (free-handle n)
  (values))

(defun sharpsign-question-mark (s c n)
  (declare (ignore s c))
  (handle-object n))

(defun left-curly-bracket (stream char)
  (declare (ignore char))
  (let ((items (read-delimited-list #\} stream t))
        (table (make-hash-table :test #'equal)))
    (loop for (key value) on items by #'cddr do
      (setf (gethash key table) value))
    table))

(define-condition unmatched-closing-curly-bracket
    (reader-error)
  ()
  (:report
   (lambda (condition stream)
     (format stream "Unmatched closing curly bracket on ~S."
             (stream-error-stream condition)))))

(defun right-curly-bracket (stream char)
  (declare (ignore char))
  (error 'unmatched-closing-curly-bracket
         :stream stream))

(defvar *cl4py-readtable*
  (let ((r (copy-readtable)))
    (set-dispatch-macro-character #\# #\! 'sharpsign-exclamation-mark r)
    (set-dispatch-macro-character #\# #\? 'sharpsign-question-mark r)
    (set-macro-character #\{ 'left-curly-bracket nil r)
    (set-macro-character #\} 'right-curly-bracket nil r)
    (values r)))

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;;
;;; Printing for Python
;;;
;;; Not all Lisp objects can be communicated to Python.  Most notably,
;;; functions and CLOS instances. Instead, we walk all objects before
;;; sending them to Python and replace occurrences of non serializable
;;; objects with reference handles.
;;;
;;; The printed structure is scanned first, such that circular structure
;;; can be printed correctly using #N= and #N#.

;;; Each entry in the table is either the value T, meaning the object has
;;; been visited once, or its ID (an integer), meaning the object has been
;;; scanned multiple times.  A negative ID means that the object has been
;;; printed at least once.

(defvar *pyprint-table*)

(defvar *pyprint-counter*)

;; We use this dummy package during printing, to have each symbol written
;; with its full package prefix.
(defpackage #:cl4py-empty-package)

(defgeneric pyprint-scan (object))

(defgeneric pyprint-write (object stream))

(defun pyprint (object &optional (stream *standard-output*))
  (let ((*pyprint-table* (make-hash-table :test #'eql))
        (*pyprint-counter* 0)
        (*package* (find-package '#:cl4py-empty-package)))
    (pyprint-scan object)
    (pyprint-write object stream)
    object))

(defmethod pyprint-scan :around ((object t))
  (unless (or (symbolp object)
              (numberp object)
              (characterp object))
    (multiple-value-bind (value present-p)
        (gethash object *pyprint-table*)
      (cond ((not present-p)
             (setf (gethash object *pyprint-table*) t)
             (call-next-method))
            ((eq value t)
             (setf (gethash object *pyprint-table*)
                   (incf *pyprint-counter*))))
      (values))))

(defmethod pyprint-scan ((object t))
  (declare (ignore object)))

(defmethod pyprint-scan ((cons cons))
  (pyprint-scan (car cons))
  (pyprint-scan (cdr cons)))

(defmethod pyprint-scan ((sequence sequence))
  (map nil #'pyprint-scan sequence))

(defmethod pyprint-scan ((hash-table hash-table))
  (when (eq (hash-table-test hash-table) 'equal)
    (maphash
     (lambda (key value)
       (pyprint-scan key)
       (pyprint-scan value))
     hash-table)))

(defmethod pyprint-scan ((package package))
  (loop for symbol being each external-symbol of package
        when (fboundp symbol)
          unless (macro-function symbol)
            unless (special-operator-p symbol) do
              (pyprint-scan (symbol-function symbol))))

(defmethod pyprint-write :around ((object t) stream)
  (let ((id (gethash object *pyprint-table*)))
    (if (integerp id)
        (cond ((plusp id)
               (setf (gethash object *pyprint-table*) (- id))
               (format stream "#~D=" id)
               (call-next-method))
              ((minusp id)
               (format stream "#~D#" (- id))))
        (call-next-method))))

(defmethod pyprint-write ((object t) stream)
  (write-char #\# stream)
  (prin1 (object-handle object) stream)
  (write-char #\? stream))

(defmethod pyprint-write ((number number) stream)
  (write number :stream stream))

(defmethod pyprint-write ((symbol symbol) stream)
  (write symbol :stream stream))

(defmethod pyprint-write ((string string) stream)
  (write string :stream stream))

(defmethod pyprint-write ((package package) stream)
  (write-string "#M" stream)
  (pyprint-write
   (list*
    (package-name package)
    (loop for symbol being each external-symbol of package
          when (fboundp symbol)
            unless (macro-function symbol)
              unless (special-operator-p symbol)
                collect (cons (symbol-name symbol)
                              (symbol-function symbol))))
   stream))

(defmethod pyprint-write ((cons cons) stream)
  (write-string "(" stream)
  (loop for car = (car cons)
        for cdr = (cdr cons) do
          (pyprint-write car stream)
          (write-string " " stream)
          (cond ((null cdr)
                 (loop-finish))
                ((or (atom cdr)
                     (integerp (gethash cdr *pyprint-table*)))
                 (write-string " . " stream)
                 (pyprint-write cdr stream)
                 (loop-finish))
                (t
                 (setf cons cdr))))
  (write-string ")" stream))

(defmethod pyprint-write ((simple-vector simple-vector) stream)
  (write-string "#(" stream)
  (loop for elt across simple-vector do
    (pyprint-write elt stream)
    (write-char #\space stream))
  (write-string ")" stream))

(defmethod pyprint-write ((hash-table hash-table) stream)
  (cond ((eql (hash-table-test hash-table) 'equal)
         (write-string "{" stream)
         (maphash
          (lambda (key value)
            (pyprint-write key stream)
            (write-char #\space stream)
            (pyprint-write value stream)
            (write-char #\space stream))
          hash-table)
         (write-string "}" stream))
        (t
         (call-next-method))))

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;;
;;; The cl4py REPL

(defgeneric condition-string (condition))

(defmethod condition-string ((condition condition))
  (with-output-to-string (stream)
    (terpri stream)
    (describe condition stream)))

(defmethod condition-string ((simple-condition simple-condition))
  (apply #'format nil
         (simple-condition-format-control simple-condition)
         (simple-condition-format-arguments simple-condition)))

(defun cl4py (&rest args)
  (declare (ignore args))
  (loop
    (let ((*package* (find-package "CL-USER")))
      (multiple-value-bind (value condition)
          (let ((*standard-output* (make-broadcast-stream))
                (*trace-output* (make-broadcast-stream))
                (*readtable* *cl4py-readtable*)
                (*read-default-float-format* 'double-float))
            (ignore-errors
             (unwind-protect (values (eval (read)))
               (clear-input))))
        (let ((*read-eval* nil)
              (*print-circle* t))
          ;; The name of the current package.
          (pyprint (package-name *package*))
          (terpri)
          ;; The value.
          (pyprint value)
          (terpri)
          ;; the error code
          (if (not condition)
              (pyprint nil)
              (pyprint
               (list (class-name (class-of condition))
                     (condition-string condition))))
          (terpri)
          (finish-output))))))

(cl4py)
