from typing import Any, List, Dict, Generic, TypeVar
import traceback

import unittest

T = TypeVar("T")
E = TypeVar("E")

class Result(Generic[T]):
    def __init__(
            self,
            value: T,
            failed: bool = False,
            failure: Dict[str, Any] | None = None,
    ) -> None:
        self.value: Any = value
        self.failed: bool = failed
        self.failure: Any = failure

    def __repr__(self) -> str:
        return (
            f"Result(value={self.value}, is_failed={self.failed}, "
            f"failure={self.failure})"
        )

    def unwrap(self) -> Any:
        return self.value

    def is_ok(self) -> bool:
        return not self.failed

    def is_err(self) -> bool:
        return self.failed

    def bind(self, func, *args, **kwargs) -> "Result":
        if self.failed:
            return self
        try:
            return Result(func(self.value, *args, **kwargs))
        except Exception as Err:
            failure = {
                    "trace": traceback.format_exc(),
                    "exception": Err,
                    "args": args,
                    "kwargs": kwargs,
                }
            return Result(None, True, failure)

    def flatten(self) -> "List[Result]":
        if isinstance(self.value, list):
            y = [Result(v) for v in self.value]
            return y
        else:
            return [self]

    def __rshift__(self, func, *args, **kwargs) -> "Result":
        return self.bind(func, *args, **kwargs)

    def __or__(self) -> "List[Result]":
        return self.flatten()

    def __eq__(self, __o: "Result") -> bool:
        if not isinstance(__o, Result):
            raise ValueError("Can only compare two Result objects")
        return self.unwrap() == __o.unwrap()


class TestResultClass(unittest.TestCase):

    def test_sucessful_assignment(self):
        self.assertEqual(Result(2).unwrap(), 2)

    def test_correct_binding(self):
        one = Result(5).bind(lambda x: x ** 2)
        self.assertEqual(one.unwrap(), 25)

    def test_binding_with_rshift(self):
        one = Result(5) >> (lambda x: x ** 2)
        self.assertEqual(one.unwrap(), 25)

    def test_flatten(self):
        flattened_result = Result(5).bind(lambda x: [x, x ** 2]).flatten()
        new_list = [Result(5), Result(25)]

        self.assertListEqual(flattened_result, new_list)


if __name__ == "__main__":
    unittest.main()
