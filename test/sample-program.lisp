(in-package :common-lisp-user)

(defun foo-{a7lkj9lakj} ()
  nil)

(defun make-error ()
  (error "Artificial error"))

(defun make-type-error ()
  (error 'type-error :datum 'fake-variable :expected-type t)
  )

(export '(make-error make-type-error))
