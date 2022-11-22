from typing import Any, List, Dict
import traceback
from .Result import Result
from itertools import compress


class MonadicListOfResult(List[Result]):
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

    def __repr__(self) -> str:
        return (
            f"MList({self.value}, is_failed={self.is_failed()}, "
            f"failure={self.failure})"
        )

    def unwrap(self) -> List[Result]:
        return self.value

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



# TODO: Write nit tests

if __name__ == "__main__":
    # testing creation of MonadicListOfResult
    # should only take a list of all results or a list of no results
    l_r = [Result(x) for x in range(3)]
    l_no_r = [0, 1, 2]
    l_mix_one = [0, Result(1), 2]

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

    try:
        l_one = MonadicListOfResult(l_r)
    except Exception as Err:
        print(Err)

    try:
        l_one = MonadicListOfResult(l_no_r)
    except Exception as Err:
        print(Err)

    try:
        l_one = MonadicListOfResult(l_mix_one)
    except Exception as Err:
        print(Err)

    # testing filter
    my_l = MonadicListOfResult(list(range(10)))
    print(my_l)
    print(my_l.bind(lambda x: x % 2 == 0))
    
    # print(my_l)
    print(my_l.filter(lambda x: x % 2 == 0))
