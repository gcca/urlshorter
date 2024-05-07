#define PY_SSIZE_T_CLEAN
#include <Python.h>

static constexpr std::size_t size = 7;
static constexpr Py_UCS4 maxchar = 127;
static constexpr char charsmap[] =
    "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ";
static constexpr std::size_t numeric_base = sizeof(charsmap) - 1;

static PyObject *ShortUrl(PyObject *, PyObject *args) {
  if (not PyTuple_Check(args)) {
    PyErr_BadInternalCall();
    return nullptr;
  }

  if (Py_SIZE(args) != 1) {
    PyErr_SetString(PyExc_ValueError, "Call error. Use: short.ShortUrl(int)");
    return nullptr;
  }

  PyObject *arg = reinterpret_cast<PyTupleObject *>(args)->ob_item[0];

  if (not PyLong_CheckExact(arg)) {
    PyErr_SetString(PyExc_TypeError, "Argument not int error");
    return nullptr;
  }

  std::size_t uid = PyLong_AsSize_t(arg);

  PyObject *shorturl = PyUnicode_New(size, maxchar);
  if (shorturl == nullptr) {
    return nullptr;
  }

  Py_UCS1 *p = PyUnicode_1BYTE_DATA(shorturl);
  Py_UCS1 *q = p + size;

  do {
    *--q = charsmap[uid % numeric_base];
    uid /= numeric_base;
  } while (uid > 0);

  while (p < q)
    *--q = '0';

  return shorturl;
}

static PyMethodDef ShortMethods[] = {{"ShortUrl", ShortUrl, METH_VARARGS, ""},
                                     {nullptr, nullptr, 0, nullptr}};

static PyModuleDef ShortModule = {PyModuleDef_HEAD_INIT, "short",
                                  "Short Module", -1, ShortMethods};

PyMODINIT_FUNC PyInit_short(void) { return PyModule_Create(&ShortModule); }
