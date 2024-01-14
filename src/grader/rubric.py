from typing import List, Optional
import logging

from grader.utils import *


class RubricItem:
    def __init__(
        self,
        name: str,
        output: str = None,
        input: str = None,
        score: int = 0,
        max_score: Optional[int] = None,
        passed: Optional[bool] = None,
        visibility: str = "visible",
    ):
        assert visibility in [
            Rubric.VIS_VISIBLE,
            Rubric.VIS_AFT_DUE,
            Rubric.VIS_AFT_PUBLISH,
            Rubric.VIS_HIDDEN,
        ]
        self.name: str = name
        self.output: str = output
        self.input: str = input
        self.score: int = score
        self.passed: bool = passed
        self.visibility: str = visibility
        self.max_score: Optional[int] = max_score

    def as_dict(self):
        rubric_item = {
            "name": self.name,
            "score": self.score,
            "visibility": self.visibility,
        }
        if self.passed is not None:
            rubric_item["status"] = "passed" if self.passed else "failed"
        if self.output is not None:
            rubric_item["output"] = self.output
        if self.input is not None:
            rubric_item["input"] = self.input
        if self.max_score is not None:
            rubric_item["max_score"] = self.max_score
        return rubric_item


class Rubric:
    VIS_VISIBLE = "visible"
    VIS_HIDDEN = "hidden"
    VIS_AFT_DUE = "after_due_date"
    VIS_AFT_PUBLISH = "after_published"

    def __init__(self, name: str, hide_scores=False):
        self.name: str = name
        self.rubric_items: List[RubricItem] = []
        self.hide_scores = hide_scores
        self._score_for_logging = 0

    def add_item(
        self,
        name: str,
        output: str = "",
        input: str = "",
        score: int = 0,
        max_score: Optional[int] = None,
        passed: Optional[bool] = None,
        visibility: str = VIS_VISIBLE,
    ):
        logging.info(
            f"Rubric: {self.name} - Adding rubric item {name=} {score=} {passed=}"
        )
        self.rubric_items.append(
            RubricItem(
                name=f"{self.name}: {name}",
                output=output,
                input=input,
                score=score if not self.hide_scores else 0,
                max_score=max_score,
                passed=passed,
                visibility=visibility,
            )
        )
        self._score_for_logging += score

    def export(self):
        logging.info(f"Rubric: {self.name} - Total score: {self._score_for_logging}")
        return [ri.as_dict() for ri in self.rubric_items]
