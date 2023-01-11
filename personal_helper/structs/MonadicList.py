from typing import Any, List, Dict, Tuple, Set
import traceback
from itertools import compress

class MonadicList():
    def __init__(
        self,
        value: List[Any] | Tuple[Any] | Set[Any],
        failed: bool = False,
        failure: Dict[str, Any] = {}
    ) -> None:
        is_list = isinstance(value, list)
        is_tuple = isinstance(value, tuple)
        is_set = isinstance(value, set)
        if not (is_list or is_tuple or is_set):
            raise ValueError(
                "value should be a list of elements all of the same type"
            )

        value_type_counts = {}

        for i in value:
            curr_type = type(i)
            try:
                value_type_counts[curr_type] += 1
            except KeyError:
                value_type_counts[curr_type] = 1
            del curr_type

        if len(value_type_counts) > 1:
            pretty_print_dict = "\n\t".join([
                f"{k}: {v}" for k, v in value_type_counts.items()
            ])
            raise ValueError(
                "All elements in the list should be of the same type. List "
                "passed contains the following type counts:\n\t"
                f"{pretty_print_dict}\n"
            )

        self.value = value if is_list else list(value)
        self.failed = True if failed else False
        self.failure = failure

        # for iteration
        self.counter: int = 0
        self.iter_len: int = 0

    def __repr__(self) -> str:
        pretty = self._pretty_print_failure(indent_depth=1)
        msg = (
                f"MonadicList(\n\telements: {self.value},\n\t"
                f"is_failed: {self.is_failed()},\n\t"
                f"failures: \n\t{pretty}\n\t)"
        )
        return msg

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

    def _pretty_print_failure(self, indent_depth: int = 0) -> str:
        sep = "".join(["\n\t" for _ in range(indent_depth+1)])
        pretty = f"{sep}".join([
            f"{k}: {v}" for k, v in self.failure.items()
        ])

        return pretty

    def is_failed(self) -> bool:
        return self.failed

    def is_ok(self) -> bool:
        return not self.failed

    def unwrap(self) -> List[Any]:
        return self.value

    def bind(self, func, *args, **kwargs) -> "MonadicList":
        if self.is_failed():
            return self

        try:
            return MonadicList([
                func(v, *args, **kwargs) for v in self
            ])
        except Exception as Err:
            failure = {
                "trace": traceback.format_exc(),
                "exception": Err,
                "args": args,
                "kwargs": kwargs,
            }
            return MonadicList(self.value, True, failure)

    def flatten(self) -> "MonadicList":
        if self.is_failed():
            return self

        elements_are_iterable = [
            isinstance(v, list) or isinstance(v, tuple) for v in self.value
        ]

        are_all_iter = all(elements_are_iterable)
        if not are_all_iter:
            print(
                "Can only flatten when elements of object are lists or tuples"
            )
            return self

        try:
            flattened = []
            for v in self:
                flattened.extend(v)
            return MonadicList(flattened)
        except Exception as Err:
            failure = {
                "trace": traceback.format_exc(),
                "exception": Err,
                "args": [],
                "kwargs": {},
            }
            return MonadicList(self.value, True, failure)

    def bind_and_flatten(self, func, *args, **kwargs) -> "MonadicList":
        if self.is_failed():
            return self

        try:
            results = [func(v, *args, **kwargs) for v in self]

            elements_are_iterable = [
                isinstance(v, list) or isinstance(v, tuple) for v in self.value
            ]

            are_all_iter = all(elements_are_iterable)
            if not are_all_iter:
                print(
                    "Flattening requires all elements being list or tuple"
                )
                return MonadicList(results)

            flattened = []
            for v in results:
                flattened.extend(v)
            return MonadicList(results)

        except Exception as Err:
            failure = {
                "trace": traceback.format_exc(),
                "exception": Err,
                "args": args,
                "kwargs": kwargs,
            }
            return MonadicList(self.value, True, failure)

    def filter(self, func, *args, **kwargs) -> "MonadicList":
        if self.is_failed():
            return self

        try:
            filter_conds = [
                func(v, *args, **kwargs) for v in self
            ]
            return MonadicList(
                list(compress(self.value, filter_conds))
            )
        except Exception as Err:
            failure = {
                "trace": traceback.format_exc(),
                "exception": Err,
                "args": args,
                "kwargs": kwargs,
            }
            return MonadicList(self.value, True, failure)

    def __rshift__(self, func, *args, **kwargs) -> "MonadicList":
        return self.bind(func, *args, **kwargs)

    def __or__(self, func, *args, **kwargs) -> "MonadicList":
        return self.filter(func, *args, **kwargs)

    def __eq__(self, __o: "MonadicList") -> bool:
        if not isinstance(__o, MonadicList):
            raise ValueError("Can only compare two MonadicLists")
        return self.unwrap() == __o.unwrap()

