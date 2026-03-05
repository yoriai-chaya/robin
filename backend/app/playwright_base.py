from __future__ import annotations

from typing import List

from pydantic import BaseModel


class PwLocation(BaseModel):
    file: str
    column: int
    line: int


class PwErrorInfo(BaseModel):
    message: str | None = None
    stack: str | None = None
    location: PwLocation | None = None


class PwText(BaseModel):
    text: str | None = None


class PwResult(BaseModel):
    status: str
    errors: List[PwErrorInfo] = []
    stdout: List[PwText]
    stderr: List[PwText]


class PwTest(BaseModel):
    timeout: int
    results: List[PwResult]


class PwSpec(BaseModel):
    title: str
    ok: bool
    tests: List[PwTest]


class PwConfig(BaseModel):
    configFile: str | None = None
    rootDir: str | None = None


class PwSuite(BaseModel):
    title: str
    file: str
    specs: List[PwSpec] = []
    suites: List[PwSuite] = []


class PwStats(BaseModel):
    startTime: str
    duration: float
    expected: int
    skipped: int
    unexpected: int
    flaky: int


class PwReport(BaseModel):
    config: PwConfig
    suites: List[PwSuite] = []
    errors: List[PwErrorInfo] = []
    stats: PwStats
