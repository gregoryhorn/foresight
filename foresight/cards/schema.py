"""Finite data-only tiny-test mappings, never shell templates or dynamic imports."""
import re
from typing import Literal
from pydantic import Field, model_validator
from pydantic import BaseModel, ConfigDict


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class Mapping(Strict):
    family: Literal['fixed-argv-media-v1'] = 'fixed-argv-media-v1'
    executable: Literal['sox', 'magick', 'espeak', 'flite', 'ffmpeg']
    operation: str = Field(min_length=1, max_length=120)
    arguments: list[str] = Field(min_length=1, max_length=24)
    format: Literal['wav', 'png', 'mp4']
    version: str = Field(min_length=1, max_length=64)
    cost: Literal['zero', 'unknown'] = 'unknown'
    seconds: float = Field(ge=0, le=1, default=0)
    shape: str = Field(max_length=40)

    @model_validator(mode='after')
    def finite(self):
        if self.executable == 'ffmpeg':
            if self.format != 'mp4' or self.arguments != ['-v','error','-f','lavfi','-i',
                'color=c=blue:s=160x90:d=0.6','-c:v','libx264','-pix_fmt','yuv420p','{output}']:
                raise ValueError('Only the fixed tiny FFmpeg color test is supported')
            return self
        if self.format == 'mp4':
            raise ValueError('MP4 is limited to the fixed FFmpeg test')
        if self.arguments.count('{output}') != 1:
            raise ValueError('One allocated output is required')
        for token in self.arguments:
            if token == '{output}':
                continue
            # Deliberately narrow local literals: no path, URL, indirect file,
            # expansion, pipe, option assignment or command syntax from docs.
            if not re.fullmatch(r'(?:[A-Za-z0-9_.+-]{1,60}|xc:(?:blue|red|white|black))', token):
                raise ValueError('Unsupported argument primitive')
        if self.cost == 'zero' and self.seconds > 1:
            raise ValueError('Tiny test exceeds its bound')
        return self

