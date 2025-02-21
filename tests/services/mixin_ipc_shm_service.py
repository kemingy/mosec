# Copyright 2022 MOSEC Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Test IPC shared memory storage."""

import sys
from typing import List

import numpy as np

from mosec import Server, Worker
from mosec.errors import ValidationError
from mosec.mixin import PlasmaShmIPCMixin, RedisShmIPCMixin


class PlasmaRandomService(PlasmaShmIPCMixin, Worker):
    def forward(self, data: List[dict]) -> List[dict]:
        try:
            result = [{"x": np.random.rand(int(req["size"]))} for req in data]
        except KeyError as err:
            raise ValidationError(err) from err
        return result


class PlasmaDummyPostprocess(PlasmaShmIPCMixin, Worker):
    """This dummy stage is added to test the shm IPC"""

    def forward(self, data: dict) -> dict:
        assert isinstance(data.get("x"), np.ndarray), f"wrong data type: {data}"
        data["x"] = data["x"].tolist()
        return data


class RedisRandomService(RedisShmIPCMixin, Worker):
    def forward(self, data: List[dict]) -> List[dict]:
        try:
            result = [{"x": np.random.rand(int(req["size"]))} for req in data]
        except KeyError as err:
            raise ValidationError(err) from err
        return result


class RedisDummyPostprocess(RedisShmIPCMixin, Worker):
    """This dummy stage is added to test the shm IPC"""

    def forward(self, data: dict) -> dict:
        assert isinstance(data.get("x"), np.ndarray), f"wrong data type: {data}"
        data["x"] = data["x"].tolist()
        return data


def start_redis_shm_mosec():
    # configure the plasma service path
    # this assumes the redis server is running at `localhost:6379`
    RedisShmIPCMixin.set_redis_url("redis://localhost:6379/0")

    server = Server()
    server.append_worker(RedisRandomService, max_batch_size=8)
    server.append_worker(RedisDummyPostprocess, num=2)
    server.run()


def start_plasma_shm_mosec():
    from pyarrow import plasma  # type: ignore

    # initialize a 20Mb object store as shared memory
    with plasma.start_plasma_store(plasma_store_memory=20 * 1000 * 1000) as (
        shm_path,
        shm_process,
    ):
        # configure the plasma shm path
        PlasmaShmIPCMixin.set_plasma_path(shm_path)

        server = Server()
        server.register_daemon("plasma_server", shm_process)
        server.append_worker(PlasmaRandomService, max_batch_size=8)
        server.append_worker(PlasmaDummyPostprocess, num=2)
        server.run()


if __name__ == "__main__":
    if len(sys.argv) <= 1:
        print("Please specify a shm storage service to run: plasma or redis")
        sys.exit(1)

    SERVICE = sys.argv[1]
    if SERVICE == "plasma":
        start_plasma_shm_mosec()
    elif SERVICE == "redis":
        start_redis_shm_mosec()
