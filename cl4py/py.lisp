(defpackage #:cl4py
  (:use #:common-lisp)
  (:export #:cl4py))

(in-package #:cl4py)

;;; Welcome to the Lisp side of cl4py. Basically, this is just a REPL that
;;; reads expressions from the Python side and prints results back to
;;; Python.
;;;
;;; One challenge is that not all objects in Lisp can be written
;;; readably. As a pragmatic workaround, these objects are replaced by
;;; handles, by means of the #n? and #n! reader macros. The Python side is
;;; responsible for declaring when a handle may be deleted.

(defvar *handle-counter* 0)

(defvar *foreign-objects* (make-hash-table :test #'eql))

(defun handle-free (handle)
  (remhash handle *foreign-objects*)
  (values))

(defun handle-object (handle)
  (or (gethash handle *foreign-objects*)
      (error "Invalid Handle.")))

(defun (setf handle-object) (value handle)
  (setf (gethash handle *foreign-objects*) value))

(defstruct handle-wrapper (handle nil))

(defmethod print-object ((object handle-wrapper) stream)
  (write-char #\# stream)
  (prin1 (handle-wrapper-handle object) stream)
  (write-char #\? stream))

(defun register-foreign-object (object)
  (let ((handle (incf *handle-counter*)))
    (setf (handle-object handle) object)
    (make-handle-wrapper :handle handle)))

(defun sharpsign-exclamation-mark (s c n)
  (declare (ignore s c))
  (handle-free n))

(defun sharpsign-questionmark (s c n)
  (declare (ignore s c))
  (handle-object n))

(defvar *cl4py-readtable*
  (let ((r (copy-readtable)))
    (set-dispatch-macro-character #\# #\! #'sharpsign-exclamation-mark r)
    (set-dispatch-macro-character #\# #\? #'sharpsign-questionmark r)
    (values r)))

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;;
;;; Wrapping Foreign Objects
;;;
;;; Not all Lisp objects can communicated to Python. Most notably,
;;; functions and CLOS instances. Instead, we walk all objects before
;;; sending them to Python and replace occurrences of non serializable
;;; objects with reference handles.

(defgeneric wrap-foreign-objects (object))

(defmethod wrap-foreign-objects ((object t))
  (register-foreign-object object))

(defmethod wrap-foreign-objects ((symbol symbol))
  symbol)

(defmethod wrap-foreign-objects ((number number))
  number)

(defmethod wrap-foreign-objects ((string string))
  string)

(defmethod wrap-foreign-objects ((hash-table hash-table))
  ;; TODO
  hash-table)

(defmethod wrap-foreign-objects ((cons cons))
  (cons (wrap-foreign-objects (car cons))
        (wrap-foreign-objects (cdr cons))))

(defmethod wrap-foreign-objects ((sequence sequence))
  (map (type-of sequence) #'wrap-foreign-objects sequence))

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
                (*readtable* *cl4py-readtable*))
            (ignore-errors
             (unwind-protect (values (eval (read)))
               (clear-input))))
        (let ((*read-eval* nil))
          ;; the value
          (prin1 (wrap-foreign-objects value))
          (terpri)
          ;; the error code
          (if (not condition)
              (prin1 nil)
              (prin1
               (list (class-name (class-of condition))
                     (condition-string condition))))
          (terpri)
          (finish-output))))))

(cl4py)
