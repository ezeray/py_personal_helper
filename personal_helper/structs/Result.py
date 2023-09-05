from typing import Any, Generic, TypeVar, Callable
import traceback
import unittest
import doctest

# Represents an Ok type
T = TypeVar("T")
# Represents an Err type
E = TypeVar("E")

U = TypeVar("U")


class Result(Generic[T, E]):
    """
    This is my attempt at writing a Monadic (Monad-ish?) type, based on the
    Result enum from Rust. However, there"s some additional sugar I"ve added
    based on things that I find useful, such as keeping a detailed dictionary
    with the traceback in case there"s an error encountered.

    Please note that the class cannot be initialized directly, instead use one
    of the two constructos.

    To build a Result::Ok, use the constructor method 
    """

    __slots__ = ("_value", "_is_ok", "_type", "_failure")
    def __init__(
            self,
            value: T | E,
            is_ok: bool,
            build: bool = False,
            failure: dict[str, Any] = {}
        ) -> None:
        if not build:
            raise TypeError("This class can't be initialized directly")
        self._value = value
        self._is_ok = is_ok
        self._type = type(value)
        self._failure = failure

    @classmethod
    def Ok(cls, value: T) -> "Result[T, Any]":
        return cls(value, True, build=True)

    @classmethod
    def Err(cls, err: E, failure: dict[str, Any]) -> "Result[Any, E]":
        return cls(err, False, build=True, failure=failure)

    @property
    def is_ok(self) -> bool:
        return self._is_ok

    @property
    def is_err(self) -> bool:
        return not self._is_ok

    def __repr__(self) -> str:
        return (
            f"Result({self._value=}, {self._type}, "
            f"{self._is_ok=}, {self._failure=})"
        )

    def unwrap(self) -> T:
        if self._is_ok:
            return self._value
        raise ValueError(f"Contents of Result is Err: {self._value}")

    def unwrap_err(self) -> E:
        if not self._is_ok:
            return self._value
        raise ValueError(f"Contents of Result is Ok: {self._value}")

    def unwrap_or(self, the_or: T) -> T:
        return self._value if self._is_ok else the_or


    def bind(
            self,
            func: Callable[[T, Any], U],
            *args: Any,
            **kwargs: Any
        ) -> "Result[T, E] | Result[U, E] | Result[Any, E]":
        if not self._is_ok:
            return self
        try:
            # if this is reached we can be sure that self._value will never be
            # of type E, and this will only be returned if the call succeeds
            my_val = func(self._value, *args, **kwargs) # type: ignore
            return self.Ok(my_val)
        except Exception as e:
            # similar to the case above, we are sure that this branch will only
            # be reached when there is a failure
            failure = {
                "trace": traceback.format_exc(),
                "value": self._value,
                "exception": e,
                "func": func.__name__,
                "args": args,
                "kwargs": kwargs,
            }
            return self.Err(e, failure=failure) # type: ignore

    def __rshift__(
            self,
            func: Callable[[T, Any], T | U],
            *args: Any,
            **kwargs: Any
        ) -> "Result[T, Any] | Result[U, Any] | Result[Any, E]":
        return self.bind(func, *args, **kwargs)

