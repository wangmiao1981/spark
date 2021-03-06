#
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from typing import Any, Union, cast

import pandas as pd
from pandas.api.types import CategoricalDtype

from pyspark.sql import functions as F
from pyspark.sql.types import IntegralType, StringType

from pyspark.pandas._typing import Dtype, IndexOpsLike, SeriesOrIndex
from pyspark.pandas.base import column_op, IndexOpsMixin
from pyspark.pandas.data_type_ops.base import (
    DataTypeOps,
    _as_categorical_type,
    _as_other_type,
    _as_string_type,
)
from pyspark.pandas.internal import InternalField
from pyspark.pandas.spark import functions as SF
from pyspark.pandas.typedef import extension_dtypes, pandas_on_spark_type
from pyspark.sql.types import BooleanType


class StringOps(DataTypeOps):
    """
    The class for binary operations of pandas-on-Spark objects with spark type: StringType.
    """

    @property
    def pretty_name(self) -> str:
        return "strings"

    def add(self, left: IndexOpsLike, right: Any) -> SeriesOrIndex:
        if isinstance(right, IndexOpsMixin) and isinstance(right.spark.data_type, StringType):
            return column_op(F.concat)(left, right)
        elif isinstance(right, str):
            return column_op(F.concat)(left, SF.lit(right))
        else:
            raise TypeError("string addition can only be applied to string series or literals.")

    def sub(self, left: IndexOpsLike, right: Any) -> SeriesOrIndex:
        raise TypeError("subtraction can not be applied to string series or literals.")

    def mul(self, left: IndexOpsLike, right: Any) -> SeriesOrIndex:
        if isinstance(right, str):
            raise TypeError("multiplication can not be applied to a string literal.")

        if (
            isinstance(right, IndexOpsMixin)
            and isinstance(right.spark.data_type, IntegralType)
            and not isinstance(right.dtype, CategoricalDtype)
        ) or isinstance(right, int):
            return column_op(SF.repeat)(left, right)
        else:
            raise TypeError("a string series can only be multiplied to an int series or literal")

    def truediv(self, left: IndexOpsLike, right: Any) -> SeriesOrIndex:
        raise TypeError("division can not be applied on string series or literals.")

    def floordiv(self, left: IndexOpsLike, right: Any) -> SeriesOrIndex:
        raise TypeError("division can not be applied on string series or literals.")

    def mod(self, left: IndexOpsLike, right: Any) -> SeriesOrIndex:
        raise TypeError("modulo can not be applied on string series or literals.")

    def pow(self, left: IndexOpsLike, right: Any) -> SeriesOrIndex:
        raise TypeError("exponentiation can not be applied on string series or literals.")

    def radd(self, left: IndexOpsLike, right: Any) -> SeriesOrIndex:
        if isinstance(right, str):
            return cast(
                SeriesOrIndex,
                left._with_new_scol(F.concat(SF.lit(right), left.spark.column)),  # TODO: dtype?
            )
        else:
            raise TypeError("string addition can only be applied to string series or literals.")

    def rsub(self, left: IndexOpsLike, right: Any) -> SeriesOrIndex:
        raise TypeError("subtraction can not be applied to string series or literals.")

    def rmul(self, left: IndexOpsLike, right: Any) -> SeriesOrIndex:
        if isinstance(right, int):
            return column_op(SF.repeat)(left, right)
        else:
            raise TypeError("a string series can only be multiplied to an int series or literal")

    def rtruediv(self, left: IndexOpsLike, right: Any) -> SeriesOrIndex:
        raise TypeError("division can not be applied on string series or literals.")

    def rfloordiv(self, left: IndexOpsLike, right: Any) -> SeriesOrIndex:
        raise TypeError("division can not be applied on string series or literals.")

    def rpow(self, left: IndexOpsLike, right: Any) -> SeriesOrIndex:
        raise TypeError("exponentiation can not be applied on string series or literals.")

    def rmod(self, left: IndexOpsLike, right: Any) -> SeriesOrIndex:
        raise TypeError("modulo can not be applied on string series or literals.")

    def astype(self, index_ops: IndexOpsLike, dtype: Union[str, type, Dtype]) -> IndexOpsLike:
        dtype, spark_type = pandas_on_spark_type(dtype)

        if isinstance(dtype, CategoricalDtype):
            return _as_categorical_type(index_ops, dtype, spark_type)

        if isinstance(spark_type, BooleanType):
            if isinstance(dtype, extension_dtypes):
                scol = index_ops.spark.column.cast(spark_type)
            else:
                scol = F.when(index_ops.spark.column.isNull(), SF.lit(False)).otherwise(
                    F.length(index_ops.spark.column) > 0
                )
            return index_ops._with_new_scol(
                scol.alias(index_ops._internal.data_spark_column_names[0]),
                field=InternalField(dtype=dtype),
            )
        elif isinstance(spark_type, StringType):
            return _as_string_type(index_ops, dtype)
        else:
            return _as_other_type(index_ops, dtype, spark_type)


class StringExtensionOps(StringOps):
    """
    The class for binary operations of pandas-on-Spark objects with spark type StringType,
    and dtype StringDtype.
    """

    def restore(self, col: pd.Series) -> pd.Series:
        """Restore column when to_pandas."""
        return col.astype(self.dtype)
