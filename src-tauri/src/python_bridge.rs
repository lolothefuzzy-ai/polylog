use pyo3::prelude::*;

pub fn call_python_module(module_name: &str, function_name: &str, args: &str) -> PyResult<String> {
    Python::with_gil(|py| {
        let module = PyModule::import(py, module_name)?;
        let callable = module.getattr(function_name)?;
        let result: String = callable.call1((args,))?.extract()?;
        Ok(result)
    })
}
