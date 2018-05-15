(defpackage #:cl4py
  (:use #:common-lisp)
  (:export #:cl4py))

(in-package #:cl4py)

(defun cl4py-eval (expr)
  )

(defun cl4py (&rest args)
  (declare (ignore args))
  (loop
    (multiple-value-bind (value condition)
        (let ((*standard-output* (make-broadcast-stream))
              (*trace-output* (make-broadcast-stream)))
          (ignore-errors (eval (read))))
      (with-standard-io-syntax
        (let ((*read-eval* nil))
          ;; the value
          (prin1 value)
          (terpri)
          ;; the error code
          (prin1 (if (not condition)
                     nil
                     (class-name (class-of condition))))
          (terpri)
          ;; the package name
          (prin1 nil #+nil(package-name *package*))
          (terpri)
          (finish-output))))))

(cl4py)
