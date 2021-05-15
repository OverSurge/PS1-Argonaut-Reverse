from io import BytesIO

import pytest

from ps1_argonaut.utils import *


class TestRoundUpPadding:
    def test_round_up_padding_zero(self):
        assert round_up_padding(0) == 0

    def test_round_up_padding_multiple(self):
        assert round_up_padding(padding_size) == padding_size

    def test_round_up_padding_under_multiple(self):
        assert round_up_padding(padding_size - 1) == 2048

    def test_round_up_padding_above_multiple(self):
        assert round_up_padding(padding_size + 1) == 4096


class TestPad2048Bytes:
    @pytest.fixture
    def bio_zero(self):
        return BytesIO()

    @pytest.fixture
    def bio_multiple(self):
        bio = BytesIO()
        bio.write(b'\xFF' * padding_size)
        return bio

    @pytest.fixture
    def bio_under_multiple(self):
        bio = BytesIO()
        bio.write((padding_size - 1) * b'\xFF')
        return bio

    @pytest.fixture
    def bio_above_multiple(self):
        bio = BytesIO()
        bio.write((padding_size + 1) * b'\xFF')
        return bio

    def test_pad_out_2048_bytes_zero(self, bio_zero):
        pad_out_2048_bytes(bio_zero)
        assert bio_zero.read() == bytes()

    def test_pad_out_2048_bytes_multiple(self, bio_multiple):
        pad_out_2048_bytes(bio_multiple)
        assert bio_multiple.tell() == padding_size

    def test_pad_in_2048_bytes_under_multiple(self, bio_under_multiple):
        pad_in_2048_bytes(bio_under_multiple)
        assert bio_under_multiple.tell() == padding_size

    def test_pad_in_2048_bytes_above_multiple(self, bio_above_multiple):
        pad_in_2048_bytes(bio_above_multiple)
        assert bio_above_multiple.tell() == 2 * padding_size
