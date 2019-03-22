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

(defun sharpsign-n (s c n) ; Numpy Arrays
  (declare (ignore c n))
  (let* ((file (read s))
         (array (load-array file)))
    (delete-file file)
    array))

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
    (set-dispatch-macro-character #\# #\N 'sharpsign-n r)
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
    (terpri stream)
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

(defmethod pyprint-scan ((array array))
  (loop for index below (array-total-size array) do
    (pyprint-scan (row-major-aref array index))))

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

(defmethod pyprint-write ((character character) stream)
  (write character :stream stream))

(defmethod pyprint-write ((pathname pathname) stream)
  (pyprint-write (truename pathname) stream))

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

(defun array-contents (array)
  (labels ((contents (dimensions index)
             (if (null dimensions)
                 (row-major-aref array index)
                 (let* ((dimension (car dimensions))
                        (dimensions (cdr dimensions))
                        (count (reduce #'* dimensions)))
                   (loop for i below dimension
                         collect (contents dimensions index)
                         do (incf index count))))))
    (contents (array-dimensions array) 0)))

(defmethod pyprint-write ((array array) stream)
  (let ((dtype (ignore-errors (dtype-from-type (array-element-type array)))))
    (cond ((or (not dtype)
               (eq (dtype-type dtype) t))
           ;; Case 1 - General Arrays.
           (write-char #\# stream)
           (write (array-rank array) :stream stream)
           (write-char #\A stream)
           (pyprint-write (array-contents array) stream))
          (t
           (let ((path (format nil "/tmp/cl4py-array-~D.npy" (random most-positive-fixnum))))
             (store-array array path)
             (write-char #\# stream)
             (write-char #\N stream)
             (pyprint-write path stream))))))

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;;
;;; Fast Array Serialization
;;;
;;; The following code adds support for transmitting arrays using the Numpy
;;; file format.  It contains a copy of the systems 'ieee-floats' and
;;; 'numpy-file-format'.  Legalese:

;;; Copyright (c) 2006 Marijn Haverbeke
;;;
;;; This software is provided 'as-is', without any express or implied
;;; warranty. In no event will the authors be held liable for any
;;; damages arising from the use of this software.
;;;
;;; Permission is granted to anyone to use this software for any
;;; purpose, including commercial applications, and to alter it and
;;; redistribute it freely, subject to the following restrictions:
;;;
;;; 1. The origin of this software must not be misrepresented; you must
;;;    not claim that you wrote the original software. If you use this
;;;    software in a product, an acknowledgment in the product
;;;    documentation would be appreciated but is not required.
;;;
;;; 2. Altered source versions must be plainly marked as such, and must
;;;    not be misrepresented as being the original software.
;;;
;;; 3. This notice may not be removed or altered from any source
;;;    distribution.

(eval-when (:compile-toplevel :load-toplevel :execute)
  (defmacro make-float-converters (encoder-name
                                   decoder-name
                                   exponent-bits
                                   significand-bits
                                   support-nan-and-infinity-p)
    (let* ((total-bits (+ 1 exponent-bits significand-bits))
           (exponent-offset (1- (expt 2 (1- exponent-bits)))) ; (A)
           (sign-part `(ldb (byte 1 ,(1- total-bits)) bits))
           (exponent-part `(ldb (byte ,exponent-bits ,significand-bits) bits))
           (significand-part `(ldb (byte ,significand-bits 0) bits))
           (nan support-nan-and-infinity-p)
           (max-exponent (1- (expt 2 exponent-bits)))) ; (B)
      `(progn
         (defun ,encoder-name (float)
           ,@(unless nan `((declare (type float float))))
           (multiple-value-bind (sign significand exponent)
               (cond ,@(when nan `(((eq float :not-a-number)
                                    (values 0 1 ,max-exponent))
                                   ((eq float :positive-infinity)
                                    (values 0 0 ,max-exponent))
                                   ((eq float :negative-infinity)
                                    (values 1 0 ,max-exponent))))
                     (t
                      (multiple-value-bind (significand exponent sign) (decode-float float)
                        (let ((exponent (if (= 0 significand)
                                            exponent
                                            (+ (1- exponent) ,exponent-offset)))
                              (sign (if (= sign 1.0) 0 1)))
                          (unless (< exponent ,(expt 2 exponent-bits))
                            (error "Floating point overflow when encoding ~A." float))
                          (if (<= exponent 0) ; (C)
                              (values sign (ash (round (* ,(expt 2 significand-bits) significand)) exponent) 0)
                              (values sign (round (* ,(expt 2 significand-bits) (1- (* significand 2)))) exponent))))))
             (let ((bits 0))
               (declare (type (unsigned-byte ,total-bits) bits))
               (setf ,sign-part sign
                     ,exponent-part exponent
                     ,significand-part significand)
               bits)))

         (defun ,decoder-name (bits)
           (declare (type (unsigned-byte ,total-bits) bits))
           (let* ((sign ,sign-part)
                  (exponent ,exponent-part)
                  (significand ,significand-part))
             ,@(when nan `((when (= exponent ,max-exponent)
                             (return-from ,decoder-name
                               (cond ((not (zerop significand)) :not-a-number)
                                     ((zerop sign) :positive-infinity)
                                     (t :negative-infinity))))))
             (if (zerop exponent)       ; (D)
                 (setf exponent 1)
                 (setf (ldb (byte 1 ,significand-bits) significand) 1))
             (let ((float-significand (float significand ,(if (> total-bits 32) 1.0d0 1.0f0))))
               (scale-float (if (zerop sign) float-significand (- float-significand))
                            (- exponent ,(+ exponent-offset significand-bits)))))))))) ; (E)

;; And instances of the above for the common forms of floats.
(declaim (inline encode-float32 decode-float32 encode-float64 decode-float64))
(make-float-converters encode-float32 decode-float32 8 23 nil)
(make-float-converters encode-float64 decode-float64 11 52 nil)

(defconstant +endianness+
  #+little-endian :little-endian
  #+bit-endian :big-endian)

(defgeneric dtype-name (dtype))

(defgeneric dtype-endianness (dtype))

(defgeneric dtype-type (dtype))

(defgeneric dtype-code (dtype))

(defgeneric dtype-size (dtype))

(defparameter *dtypes* '())

(defclass dtype ()
  ((%type :initarg :type :reader dtype-type)
   (%code :initarg :code :reader dtype-code)
   (%size :initarg :size :reader dtype-size)
   (%endianness :initarg :endianness :reader dtype-endianness)))

(defmethod print-object ((dtype dtype) stream)
  (print-unreadable-object (dtype stream :type t)
    (prin1 (dtype-code dtype) stream)))

(defun dtype-from-code (code)
  (or (find code *dtypes* :key #'dtype-code :test #'string=)
      (error "Cannot find dtype for the code ~S." code)))

(defun dtype-from-type (type)
  (or (find-if
       (lambda (dtype)
         (and (eq (dtype-endianness dtype) +endianness+)
              (subtypep type (dtype-type dtype))))
       *dtypes*)
      (error "Cannot find dtype for type ~S." type)))

(defun define-dtype (code type size &optional endianness)
  (let ((dtype (make-instance 'dtype
                 :code code
                 :type type
                 :size size
                 :endianness endianness)))
    (pushnew dtype *dtypes* :key #'dtype-code :test #'string=)
    dtype))

(defun define-multibyte-dtype (code type size)
  (define-dtype (concatenate 'string "<" code) type size :little-endian)
  (define-dtype (concatenate 'string ">" code) type size :big-endian)
  (define-dtype code type size +endianness+)
  (define-dtype (concatenate 'string "|" code) type size)
  (define-dtype (concatenate 'string "=" code) type size +endianness+))

(define-dtype "O" 't 64)
(define-dtype "?" 'bit 1)
(define-dtype "b" '(unsigned-byte 8) 8)
(define-multibyte-dtype "i1" '(signed-byte 8) 8)
(define-multibyte-dtype "i2" '(signed-byte 16) 16)
(define-multibyte-dtype "i4" '(signed-byte 32) 32)
(define-multibyte-dtype "i8" '(signed-byte 64) 64)
(define-multibyte-dtype "u1" '(unsigned-byte 8) 8)
(define-multibyte-dtype "u2" '(unsigned-byte 16) 16)
(define-multibyte-dtype "u4" '(unsigned-byte 32) 32)
(define-multibyte-dtype "u8" '(unsigned-byte 64) 64)
(define-multibyte-dtype "f4" 'single-float 32)
(define-multibyte-dtype "f8" 'double-float 64)
(define-multibyte-dtype "c8" '(complex single-float) 64)
(define-multibyte-dtype "c16" '(complex double-float) 128)

;; Finally, let's sort *dtypes* such that type queries always find the most
;; specific entry first.
(setf *dtypes* (stable-sort *dtypes* #'subtypep :key #'dtype-type))

(defun read-python-object (stream &optional (skip #\,) (stop nil))
  (loop for c = (read-char stream) do
    (case c
      ((#\space #\tab) (values))
      ((#\' #\") (return (read-python-string c stream)))
      (#\( (return (read-python-tuple stream)))
      (#\[ (return (read-python-list stream)))
      (#\{ (return (read-python-dict stream)))
      ((#\T #\F)
       (unread-char c stream)
       (return (read-python-boolean stream)))
      (otherwise
       (cond ((eql c skip)
              (return (read-python-object stream nil stop)))
             ((eql c stop)
              (return stop))
             ((digit-char-p c)
              (unread-char c stream)
              (return (read-python-integer stream)))
             (t
              (error "Invalid character: ~S" c)))))))

(defun read-python-string (delimiter stream)
  (coerce
   (loop for c = (read-char stream)
         while (char/= c delimiter)
         collect c)
   'string))

(defun read-python-integer (stream)
  (let ((result 0))
    (loop for c = (read-char stream) do
      (let ((weight (digit-char-p c)))
        (if (null weight)
            (progn
              (unread-char c stream)
              (loop-finish))
            (setf result (+ (* result 10) weight)))))
    result))

(defun read-python-boolean (stream)
  (flet ((skip (string)
           (loop for c across string do
             (assert (char= (read-char stream) c)))))
    (ecase (read-char stream)
      (#\T (skip "rue") t)
      (#\F (skip "alse") nil))))

(defun read-python-tuple (stream)
  (loop for object = (read-python-object stream nil #\))
        then (read-python-object stream #\, #\))
        until (eql object #\))
        collect object))

(defun read-python-list (stream)
  (coerce
   (loop for object = (read-python-object stream nil #\])
           then (read-python-object stream #\, #\])
         until (eql object #\])
         collect object)
   'vector))

(defun read-python-dict (stream)
  (let ((dict (make-hash-table :test #'equal)))
    (loop
      (let ((key (read-python-object stream #\, #\})))
        (when (eql key #\})
          (return dict))
        (setf (gethash key dict)
              (read-python-object stream #\:))))))

(defun read-python-object-from-string (string)
  (with-input-from-string (stream string)
    (read-python-object stream)))

(defun load-array-metadata (filename)
  (with-open-file (stream filename :direction :input :element-type '(unsigned-byte 8))
    ;; The first 6 bytes are a magic string: exactly \x93NUMPY.
    (unless (and (eql (read-byte stream) #x93)
                 (eql (read-byte stream) 78)  ; N
                 (eql (read-byte stream) 85)  ; U
                 (eql (read-byte stream) 77)  ; M
                 (eql (read-byte stream) 80)  ; P
                 (eql (read-byte stream) 89)) ; Y
      (error "Not a Numpy file."))
    (let* (;; The next 1 byte is an unsigned byte: the major version number
           ;; of the file format, e.g. \x01.
           (major-version (read-byte stream))
           ;; The next 1 byte is an unsigned byte: the minor version number
           ;; of the file format, e.g. \x00.
           (minor-version (read-byte stream))
           (header-len
             (if (= major-version 1)
                 ;; Version 1.0: The next 2 bytes form a little-endian
                 ;; unsigned int: the length of the header data HEADER_LEN.
                 (logior (ash (read-byte stream) 0)
                         (ash (read-byte stream) 8))
                 ;; Version 2.0: The next 4 bytes form a little-endian
                 ;; unsigned int: the length of the header data HEADER_LEN.
                 (logior (ash (read-byte stream) 0)
                         (ash (read-byte stream) 8)
                         (ash (read-byte stream) 16)
                         (ash (read-byte stream) 24)))))
      (declare (ignore minor-version))
      ;; The next HEADER_LEN bytes form the header data describing the
      ;; array’s format. It is an ASCII string which contains a Python
      ;; literal expression of a dictionary. It is terminated by a newline
      ;; (\n) and padded with spaces (\x20) to make the total of len(magic
      ;; string) + 2 + len(length) + HEADER_LEN be evenly divisible by 64
      ;; for alignment purposes.
      (let ((dict (read-python-object-from-string
                   (let ((buffer (make-string header-len :element-type 'base-char)))
                     (loop for index from 0 below header-len do
                       (setf (schar buffer index) (code-char (read-byte stream))))
                     buffer))))
        (values
         (gethash "shape" dict)
         (dtype-from-code (gethash "descr" dict))
         (gethash "fortran_order" dict)
         (* 8 (+ header-len (if (= 1 major-version) 10 12))))))))

(defun load-array (filename)
  ;; We actually open the file twice, once to read the metadata - one byte
  ;; at a time, and once to read the array contents with a suitable element
  ;; type (e.g. (unsigned-byte 32) for single precision floating-point
  ;; numbers).
  (multiple-value-bind (dimensions dtype fortran-order header-bits)
      (load-array-metadata filename)
    (let* ((element-type (dtype-type dtype))
           (array (make-array dimensions :element-type element-type))
           (total-size (array-total-size array))
           (chunk-size (if (subtypep element-type 'complex)
                           (/ (dtype-size dtype) 2)
                           (dtype-size dtype)))
           (stream-element-type
             (if (typep array '(array (signed-byte *)))
                 `(signed-byte ,chunk-size)
                 `(unsigned-byte ,chunk-size))))
      (unless (not fortran-order)
        (error "Reading arrays in Fortran order is not yet supported."))
      (unless (eq (dtype-endianness dtype) +endianness+)
        (error "Endianness conversion is not yet supported."))
      ;; TODO Respect fortran-order and endianness.
      (with-open-file (stream filename :element-type stream-element-type)
        ;; Skip the header.
        (loop repeat (/ header-bits chunk-size) do (read-byte stream))
        (etypecase array
          ((simple-array single-float)
           (loop for index below total-size do
             (setf (row-major-aref array index)
                   (decode-float32 (read-byte stream)))))
          ((simple-array double-float)
           (loop for index below total-size do
             (setf (row-major-aref array index)
                   (decode-float64 (read-byte stream)))))
          ((simple-array (complex single-float))
           (loop for index below total-size do
             (setf (row-major-aref array index)
                   (complex
                    (decode-float32 (read-byte stream))
                    (decode-float32 (read-byte stream))))))
          ((simple-array (complex double-float))
           (loop for index below total-size do
             (setf (row-major-aref array index)
                   (complex
                    (decode-float64 (read-byte stream))
                    (decode-float64 (read-byte stream))))))
          ((simple-array *)
           (loop for index below total-size do
             (setf (row-major-aref array index)
                   (read-byte stream))))))
      array)))

(defun array-metadata-string (array)
  (with-output-to-string (stream nil :element-type 'base-char)
    (format stream "{'descr': '~A', ~
                     'fortran_order': ~:[False~;True~], ~
                     'shape': (~{~D~^, ~}), }"
            (dtype-code (dtype-from-type (array-element-type array)))
            nil
            (array-dimensions array))))

(defun store-array (array filename)
  ;; We open the file twice - once with a stream element type of
  ;; (unsigned-byte 8) to write the header, and once with a stream element
  ;; type suitable for writing the array content.
  (let* ((dtype (dtype-from-type (array-element-type array)))
         (metadata (array-metadata-string array))
         (metadata-length (- (* 64 (ceiling (+ 10 (length metadata)) 64)) 10)))
    (with-open-file (stream filename :direction :output
                                     :element-type '(unsigned-byte 8)
                                     :if-exists :supersede)
      (write-sequence #(#x93 78 85 77 80 89) stream) ; The magic string.
      (write-byte 1 stream) ; Major version.
      (write-byte 0 stream) ; Minor version.
      ;; Write the length of the metadata string (2 bytes, little endian).
      (write-byte (ldb (byte 8 0) metadata-length) stream)
      (write-byte (ldb (byte 8 8) metadata-length) stream)
      ;; Write the metadata string.
      (loop for char across metadata do
        (write-byte (char-code char) stream))
      ;; Pad the header with spaces for 64 byte alignment.
      (loop repeat (- metadata-length (length metadata) 1) do
        (write-byte (char-code #\space) stream))
      (write-byte (char-code #\newline) stream)) ; Finish with a newline.
    ;; Now, open the file a second time to write the array contents.
    (let* ((chunk-size (if (subtypep (array-element-type array) 'complex)
                           (/ (dtype-size dtype) 2)
                           (dtype-size dtype)))
           (stream-element-type
             (if (typep array '(array (signed-byte *)))
                 `(signed-byte ,chunk-size)
                 `(unsigned-byte ,chunk-size)))
           (total-size (array-total-size array)))
      (with-open-file (stream filename :direction :output
                                       :element-type stream-element-type
                                       :if-exists :append)
        (etypecase array
          ((simple-array single-float)
           (loop for index below total-size do
             (write-byte (encode-float32 (row-major-aref array index)) stream)))
          ((simple-array double-float)
           (loop for index below total-size do
             (write-byte (encode-float64 (row-major-aref array index)) stream)))
          ((simple-array (complex single-float))
           (loop for index below total-size do
             (let ((c (row-major-aref array index)))
               (write-byte (encode-float32 (realpart c)) stream)
               (write-byte (encode-float32 (imagpart c)) stream))))
          ((simple-array (complex double-float))
           (loop for index below total-size do
             (let ((c (row-major-aref array index)))
               (write-byte (encode-float64 (realpart c)) stream)
               (write-byte (encode-float64 (imagpart c)) stream))))
          ((simple-array *)
           (loop for index below total-size do
             (write-byte (row-major-aref array index) stream))))))))

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
  (let* ((python (make-two-way-stream *standard-input* *standard-output*))
         (lisp-output (make-string-output-stream))
         (*standard-output* lisp-output)
         (*trace-output* lisp-output)
         (*readtable* *cl4py-readtable*))
    (loop
      (multiple-value-bind (value condition)
          (handler-case (values (eval (read python)) nil)
            (reader-error (c)
              (clear-input python)
              (values nil c))
            (serious-condition (c)
              (values nil c)))
        (let ((*read-eval* nil)
              (*print-circle* t))
          ;; First, write the name of the current package.
          (pyprint (package-name *package*) python)
          ;; Second, write the obtained value.
          (pyprint value python)
          ;; Third, write the obtained condition, or NIL.
          (if (not condition)
              (pyprint nil python)
              (pyprint
               (list (class-name (class-of condition))
                     (condition-string condition))
               python))
          ;; Fourth, write the output that has been obtained so far.
          (pyprint (get-output-stream-string lisp-output) python)
          (finish-output python))))))

(cl4py)
