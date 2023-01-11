from typing import Any, List, Dict
import traceback
from .Result import Result
from itertools import compress

import unittest


class MonadicListOfResult():
    def __init__(
            self,
            value: List[Any],
            failed: bool = False,
            failure: Dict[str, Any] | None = None,
    ) -> None:
        if not isinstance(value, list):
            raise ValueError("value should be a list")

        all_elements_result = all([
            type(x) is Result for x in value
        ])
        no_elements_result = all([
            type(x) is not Result for x in value
        ])

        if not (all_elements_result or no_elements_result):
            raise ValueError(
                "List passed should contain either all elements of type Result"
                "or no elements of type Result, not a mixed list"
            )

        if not all_elements_result:
            value = [Result(x) for x in value]

        self.value = value
        self.failed_indices = [v.failed for v in value]
        self.failed = True if failed else any(self.failed_indices)
        self.failure = failure

        # for iteration
        self.counter: int = 0
        self.iter_len: int = 0

    def __repr__(self) -> str:
        return (
            f"MList({self.value}, is_failed={self.is_failed()}, "
            f"failure={self.failure})"
        )

    def unwrap(self) -> List[Result]:
        return self.value

    def unwrap_all(self) -> List[Any]:
        return [v.unwrap() for v in self.unwrap()]

    def is_failed(self) -> bool:
        return self.failed

    def is_ok(self) -> bool:
        return not self.failed

    def bind(self, func, *args, **kwargs):
        if self.is_failed():
            return self

        try:
            return MonadicListOfResult(
                [v.bind(func, *args, **kwargs) for v in self.value]
            )
        except Exception as Err:
            failure = {
                "trace": traceback.format_exc(),
                "exception": Err,
                "args": args,
                "kwargs": kwargs,
            }
            return MonadicListOfResult(self.value, True, failure)

    def flatten(self):
        if self.is_failed():
            return self
        flattened = []

        try:
            for v in self.value:
                flattened.extend(v.flatten())
            return MonadicListOfResult(flattened)
        except Exception as Err:
            failure = {
                "trace": traceback.format_exc(),
                "exception": Err,
                "args": [],
                "kwargs": {},
            }
            return MonadicListOfResult(self.value, True, failure)

    def bind_and_flatten(
        self,
        func,
        *args,
        **kwargs,
    ):
        if self.is_failed():
            return self

        try:
            flattened = []
            for v in self.value:
                results = v.bind(func, *args, **kwargs).flatten()
                flattened.extend(results)
            return MonadicListOfResult(flattened)

        except Exception as Err:
            failure = {
                    "trace": traceback.format_exc(),
                    "exception": Err,
                    "args": args,
                    "kwargs": kwargs,
                }

            return MonadicListOfResult(self.value, True, failure)

    def filter(self, func, *args, **kwargs):
        if self.is_failed():
            return self

        try:
            filter_conds = [
                v.bind(func, *args, **kwargs).unwrap() for v in self.value
            ]
            return MonadicListOfResult(
                list(compress(self.value, filter_conds))
            )

        except Exception as Err:
            failure = {
                    "trace": traceback.format_exc(),
                    "exception": Err,
                    "args": args,
                    "kwargs": kwargs,
                }

            return MonadicListOfResult(self.value, True, failure)

    def __rshift__(self, func, *args, **kwargs):
        return self.bind_and_flatten(func, *args, **kwargs)

    def __eq__(self, __o: "MonadicListOfResult") -> bool:
        return self.unwrap() == __o.unwrap()

    def __iter__(self):
        self.counter = 0
        self.len_iter = len(self.value)
        return self

    def __next__(self):
        if self.counter < self.len_iter:
            obj = self.value[self.counter]
            self.counter += 1
            return obj
        else:
            raise StopIteration

class TestMonadicListClass(unittest.TestCase):

    def test_init_passing_result(self):
        my_l = MonadicListOfResult([Result(x) for x in ["a", "b", "c"]])
        self.assertFalse(my_l.is_failed())

    def test_init_passing_others(self):
        my_l = [1, 2, 3]
        my_ml = MonadicListOfResult(my_l)
        self.assertEqual(my_ml.unwrap(), [Result(x) for x in my_l])

    def test_list_mixed_types_with_result_should_fail(self):
        my_l = [1, Result(2), 3]
        with self.assertRaises(ValueError):
            MonadicListOfResult(my_l)

    def test_two_ways_creating(self):
        one = MonadicListOfResult([1, 2, 3])
        two = MonadicListOfResult([Result(x) for x in range(1, 4)])
        self.assertEqual(one, two)

    def test_bind(self):
        bind_result = MonadicListOfResult([1, 2, 3]).bind(lambda x: x ** 2)
        expected_result = MonadicListOfResult([1, 4, 9])
        self.assertEqual(bind_result, expected_result)

    def test_unwrapping(self):
        bind_result = MonadicListOfResult([1, 2, 3]).bind(lambda x: x ** 2)
        expected = [Result(v) for v in [1, 4, 9]]
        self.assertEqual(bind_result.unwrap(), expected)

    def test_unwrap_all(self):
        bind_result = MonadicListOfResult([1, 2, 3]).bind(lambda x: x ** 2)
        expected = [1, 4, 9]
        self.assertEqual(bind_result.unwrap_all(), expected)

    def test_flatten(self):
        flatten_result = (
            MonadicListOfResult([1, 2, 3])
            .bind(lambda x: [x, x ** 2])
            .flatten()
        )
        expected_result = MonadicListOfResult([1, 1, 2, 4, 3, 9])
        self.assertEqual(flatten_result, expected_result)

    def test_bind_flatten(self):
        flatten_result = (
            MonadicListOfResult([1, 2, 3])
            .bind_and_flatten(lambda x: [x, x ** 2])
        )
        expected_result = MonadicListOfResult([1, 1, 2, 4, 3, 9])
        self.assertEqual(flatten_result, expected_result)

    def test_filter(self):
        result = (
            MonadicListOfResult(list(range(10)))
            .filter(lambda x: x % 2 == 0)
        )
        expected = MonadicListOfResult([0, 2, 4, 6, 8])
        self.assertEqual(result, expected)


if __name__ == "__main__":
    unittest.main()
    # testing creation of MonadicListOfResult
    # should only take a list of all results or a list of no results
    # l_r = [Result(x) for x in range(3)]
    # l_no_r = [0, 1, 2]
    # l_mix_one = [0, Result(1), 2]

    # testing basic logic
    # print(l_r)
    # l_r_all_result = all([type(x) is Result for x in l_r])
    # l_r_no_result = all([type(x) is not Result for x in l_r])
    # print(l_r_all_result or l_r_no_result)

    # l_no_r_all_result = all([type(x) is Result for x in l_no_r])
    # l_no_r_no_result = all([type(x) is not Result for x in l_no_r])
    # print(l_no_r_all_result or l_no_r_no_result)

    # print(l_mix_one)
    # l_mix_r_all_result = all([type(x) is Result for x in l_mix_one])
    # print(l_mix_r_all_result)
    # l_mix_r_no_result = all([type(x) is not Result for x in l_mix_one])
    # print(l_mix_r_no_result)
    # print(l_mix_r_all_result or l_mix_r_no_result)

    # try:
    #     l_one = MonadicListOfResult(l_r)
    # except Exception as Err:
    #     print(Err)

    # try:
    #     l_one = MonadicListOfResult(l_no_r)
    # except Exception as Err:
    #     print(Err)

    # try:
    #     l_one = MonadicListOfResult(l_mix_one)
    # except Exception as Err:
    #     print(Err)

    # # testing filter
    # my_l = MonadicListOfResult(list(range(10)))
    # print(my_l)
    # print(my_l.bind(lambda x: x % 2 == 0))

    # # print(my_l)
    # print(my_l.filter(lambda x: x % 2 == 0))
