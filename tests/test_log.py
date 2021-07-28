import contextlib
import io
import tempfile
import unittest

import crayons

import wpsync.log


class TestLogger(unittest.TestCase):
    def test_log_level(self):
        abstract_logger = wpsync.log.AbstractLogger()
        self.assertEqual(abstract_logger.level, 2)
        abstract_logger = wpsync.log.AbstractLogger(0)
        self.assertEqual(abstract_logger.level, 0)
        abstract_logger = wpsync.log.AbstractLogger(level=0)
        self.assertEqual(abstract_logger.level, 0)
        abstract_logger = wpsync.log.AbstractLogger(1)
        self.assertEqual(abstract_logger.level, 1)
        abstract_logger = wpsync.log.AbstractLogger(level=2)
        self.assertEqual(abstract_logger.level, 2)
        abstract_logger = wpsync.log.AbstractLogger(3)
        self.assertEqual(abstract_logger.level, 3)
        abstract_logger = wpsync.log.AbstractLogger(level=4)
        self.assertEqual(abstract_logger.level, 4)
        with self.assertRaises(ValueError):
            wpsync.log.AbstractLogger(-1)
        with self.assertRaises(ValueError):
            wpsync.log.AbstractLogger(level=5)
        with self.assertRaises(ValueError):
            wpsync.log.AbstractLogger(level=100)


class TestAbstractLogger(TestLogger):
    def test_init(self):
        abstract_logger = wpsync.log.AbstractLogger()
        self.assertIsInstance(abstract_logger, wpsync.log.AbstractLogger)

    def test_log_level_0(self):
        logger = wpsync.log.AbstractLogger(0)
        self.assertEqual(logger.do_log_title(), False)
        self.assertEqual(logger.do_log_step(), False)
        self.assertEqual(logger.do_log_error(), False)
        self.assertEqual(logger.do_log_warning(), False)
        self.assertEqual(logger.do_log_info(), False)
        self.assertEqual(logger.do_log_success(), False)

    def test_log_level_1(self):
        logger = wpsync.log.AbstractLogger(1)
        self.assertEqual(logger.do_log_title(), False)
        self.assertEqual(logger.do_log_step(), False)
        self.assertEqual(logger.do_log_error(), True)
        self.assertEqual(logger.do_log_warning(), False)
        self.assertEqual(logger.do_log_info(), False)
        self.assertEqual(logger.do_log_success(), False)

    def test_log_level_2(self):
        logger = wpsync.log.AbstractLogger(2)
        self.assertEqual(logger.do_log_title(), False)
        self.assertEqual(logger.do_log_step(), False)
        self.assertEqual(logger.do_log_error(), True)
        self.assertEqual(logger.do_log_warning(), True)
        self.assertEqual(logger.do_log_info(), False)
        self.assertEqual(logger.do_log_success(), False)

    def test_log_level_3(self):
        logger = wpsync.log.AbstractLogger(3)
        self.assertEqual(logger.do_log_title(), False)
        self.assertEqual(logger.do_log_step(), False)
        self.assertEqual(logger.do_log_error(), True)
        self.assertEqual(logger.do_log_warning(), True)
        self.assertEqual(logger.do_log_info(), True)
        self.assertEqual(logger.do_log_success(), False)

    def test_log_level_4(self):
        logger = wpsync.log.AbstractLogger(4)
        self.assertEqual(logger.do_log_title(), True)
        self.assertEqual(logger.do_log_step(), True)
        self.assertEqual(logger.do_log_error(), True)
        self.assertEqual(logger.do_log_warning(), True)
        self.assertEqual(logger.do_log_info(), True)
        self.assertEqual(logger.do_log_success(), True)

    def test_abstract_methods(self):
        abstract_logger = wpsync.log.AbstractLogger()
        with self.assertRaises(NotImplementedError):
            abstract_logger.title("test")
        with self.assertRaises(NotImplementedError):
            abstract_logger.step("test")
        with self.assertRaises(NotImplementedError):
            abstract_logger.error("test")
        with self.assertRaises(NotImplementedError):
            abstract_logger.warning("test")
        with self.assertRaises(NotImplementedError):
            abstract_logger.info("test")
        with self.assertRaises(NotImplementedError):
            abstract_logger.success("test")


class TestTermLogger(TestLogger):
    def test_format(self):
        term_logger = wpsync.log.TermLogger()
        self.assertIsInstance(
            term_logger.format("test"), crayons.ColoredString
        )
        self.assertEqual(term_logger.format("Test").encode("utf-8"), b"Test")
        self.assertEqual(
            term_logger.format("Test").__str__(),
            "\x1b[39m\x1b[22mTest\x1b[39m\x1b[22m",
        )
        self.assertEqual(
            term_logger.format("Test", always=True).__str__(),
            "\x1b[39m\x1b[22mTest\x1b[39m\x1b[22m",
        )
        self.assertEqual(
            term_logger.format("Test", bold=True).__str__(),
            "\x1b[39m\x1b[1mTest\x1b[39m\x1b[22m",
        )

    def test_title(self):
        term_logger = wpsync.log.TermLogger(4)
        with contextlib.redirect_stdout(io.StringIO()) as stdout_f:
            with contextlib.redirect_stderr(io.StringIO()) as stderr_f:
                term_logger.title("testytest")
        stdout = stdout_f.getvalue()
        stderr = stderr_f.getvalue()
        self.assertEqual(stdout, "➙ testytest\n")
        self.assertEqual(stderr, "")

    def test_step(self):
        term_logger = wpsync.log.TermLogger(4)
        with contextlib.redirect_stdout(io.StringIO()) as stdout_f:
            with contextlib.redirect_stderr(io.StringIO()) as stderr_f:
                term_logger.step("testytest")
        stdout = stdout_f.getvalue()
        stderr = stderr_f.getvalue()
        self.assertEqual(stdout, "• testytest\n")
        self.assertEqual(stderr, "")

    def test_error(self):
        term_logger = wpsync.log.TermLogger(4)
        with contextlib.redirect_stdout(io.StringIO()) as stdout_f:
            with contextlib.redirect_stderr(io.StringIO()) as stderr_f:
                term_logger.error("testytest")
        stdout = stdout_f.getvalue()
        stderr = stderr_f.getvalue()
        self.assertEqual(stdout, "")
        self.assertEqual(stderr, "✗ testytest\n")

    def test_warning(self):
        term_logger = wpsync.log.TermLogger(4)
        with contextlib.redirect_stdout(io.StringIO()) as stdout_f:
            with contextlib.redirect_stderr(io.StringIO()) as stderr_f:
                term_logger.warning("testytest")
        stdout = stdout_f.getvalue()
        stderr = stderr_f.getvalue()
        self.assertEqual(stdout, "")
        self.assertEqual(stderr, "⚠ testytest\n")

    def test_info(self):
        term_logger = wpsync.log.TermLogger(4)
        with contextlib.redirect_stdout(io.StringIO()) as stdout_f:
            with contextlib.redirect_stderr(io.StringIO()) as stderr_f:
                term_logger.info("testytest")
        stdout = stdout_f.getvalue()
        stderr = stderr_f.getvalue()
        self.assertEqual(stdout, "ℹ testytest\n")
        self.assertEqual(stderr, "")

    def test_log_level_0(self):
        term_logger = wpsync.log.TermLogger(0)
        with contextlib.redirect_stdout(io.StringIO()) as stdout_f1:
            with contextlib.redirect_stderr(io.StringIO()) as stderr_f1:
                term_logger.title("testytest")
        stdout = stdout_f1.getvalue()
        stderr = stderr_f1.getvalue()
        self.assertEqual(stdout, "")
        self.assertEqual(stderr, "")
        with contextlib.redirect_stdout(io.StringIO()) as stdout_f2:
            with contextlib.redirect_stderr(io.StringIO()) as stderr_f2:
                term_logger.step("testytest")
        stdout = stdout_f2.getvalue()
        stderr = stderr_f2.getvalue()
        self.assertEqual(stdout, "")
        self.assertEqual(stderr, "")
        with contextlib.redirect_stdout(io.StringIO()) as stdout_f3:
            with contextlib.redirect_stderr(io.StringIO()) as stderr_f3:
                term_logger.error("testytest")
        stdout = stdout_f3.getvalue()
        stderr = stderr_f3.getvalue()
        self.assertEqual(stdout, "")
        self.assertEqual(stderr, "")
        with contextlib.redirect_stdout(io.StringIO()) as stdout_f4:
            with contextlib.redirect_stderr(io.StringIO()) as stderr_f4:
                term_logger.warning("testytest")
        stdout = stdout_f4.getvalue()
        stderr = stderr_f4.getvalue()
        self.assertEqual(stdout, "")
        self.assertEqual(stderr, "")
        with contextlib.redirect_stdout(io.StringIO()) as stdout_f5:
            with contextlib.redirect_stderr(io.StringIO()) as stderr_f5:
                term_logger.info("testytest")
        stdout = stdout_f5.getvalue()
        stderr = stderr_f5.getvalue()
        self.assertEqual(stdout, "")
        self.assertEqual(stderr, "")
        with contextlib.redirect_stdout(io.StringIO()) as stdout_f6:
            with contextlib.redirect_stderr(io.StringIO()) as stderr_f6:
                term_logger.success("testytest")
        stdout = stdout_f6.getvalue()
        stderr = stderr_f6.getvalue()
        self.assertEqual(stdout, "")
        self.assertEqual(stderr, "")

    def test_log_level_1(self):
        term_logger = wpsync.log.TermLogger(1)
        with contextlib.redirect_stdout(io.StringIO()) as stdout_f1:
            with contextlib.redirect_stderr(io.StringIO()) as stderr_f1:
                term_logger.title("testytest")
        stdout = stdout_f1.getvalue()
        stderr = stderr_f1.getvalue()
        self.assertEqual(stdout, "")
        self.assertEqual(stderr, "")
        with contextlib.redirect_stdout(io.StringIO()) as stdout_f2:
            with contextlib.redirect_stderr(io.StringIO()) as stderr_f2:
                term_logger.step("testytest")
        stdout = stdout_f2.getvalue()
        stderr = stderr_f2.getvalue()
        self.assertEqual(stdout, "")
        self.assertEqual(stderr, "")
        with contextlib.redirect_stdout(io.StringIO()) as stdout_f3:
            with contextlib.redirect_stderr(io.StringIO()) as stderr_f3:
                term_logger.error("testytest")
        stdout = stdout_f3.getvalue()
        stderr = stderr_f3.getvalue()
        self.assertEqual(stdout, "")
        self.assertEqual(stderr, "✗ testytest\n")
        with contextlib.redirect_stdout(io.StringIO()) as stdout_f4:
            with contextlib.redirect_stderr(io.StringIO()) as stderr_f4:
                term_logger.warning("testytest")
        stdout = stdout_f4.getvalue()
        stderr = stderr_f4.getvalue()
        self.assertEqual(stdout, "")
        self.assertEqual(stderr, "")
        with contextlib.redirect_stdout(io.StringIO()) as stdout_f5:
            with contextlib.redirect_stderr(io.StringIO()) as stderr_f5:
                term_logger.info("testytest")
        stdout = stdout_f5.getvalue()
        stderr = stderr_f5.getvalue()
        self.assertEqual(stdout, "")
        self.assertEqual(stderr, "")
        with contextlib.redirect_stdout(io.StringIO()) as stdout_f6:
            with contextlib.redirect_stderr(io.StringIO()) as stderr_f6:
                term_logger.success("testytest")
        stdout = stdout_f6.getvalue()
        stderr = stderr_f6.getvalue()
        self.assertEqual(stdout, "")
        self.assertEqual(stderr, "")

    def test_log_level_2(self):
        term_logger = wpsync.log.TermLogger(2)
        with contextlib.redirect_stdout(io.StringIO()) as stdout_f1:
            with contextlib.redirect_stderr(io.StringIO()) as stderr_f1:
                term_logger.title("testytest")
        stdout = stdout_f1.getvalue()
        stderr = stderr_f1.getvalue()
        self.assertEqual(stdout, "")
        self.assertEqual(stderr, "")
        with contextlib.redirect_stdout(io.StringIO()) as stdout_f2:
            with contextlib.redirect_stderr(io.StringIO()) as stderr_f2:
                term_logger.step("testytest")
        stdout = stdout_f2.getvalue()
        stderr = stderr_f2.getvalue()
        self.assertEqual(stdout, "")
        self.assertEqual(stderr, "")
        with contextlib.redirect_stdout(io.StringIO()) as stdout_f3:
            with contextlib.redirect_stderr(io.StringIO()) as stderr_f3:
                term_logger.error("testytest")
        stdout = stdout_f3.getvalue()
        stderr = stderr_f3.getvalue()
        self.assertEqual(stdout, "")
        self.assertEqual(stderr, "✗ testytest\n")
        with contextlib.redirect_stdout(io.StringIO()) as stdout_f4:
            with contextlib.redirect_stderr(io.StringIO()) as stderr_f4:
                term_logger.warning("testytest")
        stdout = stdout_f4.getvalue()
        stderr = stderr_f4.getvalue()
        self.assertEqual(stdout, "")
        self.assertEqual(stderr, "⚠ testytest\n")
        with contextlib.redirect_stdout(io.StringIO()) as stdout_f5:
            with contextlib.redirect_stderr(io.StringIO()) as stderr_f5:
                term_logger.info("testytest")
        stdout = stdout_f5.getvalue()
        stderr = stderr_f5.getvalue()
        self.assertEqual(stdout, "")
        self.assertEqual(stderr, "")
        with contextlib.redirect_stdout(io.StringIO()) as stdout_f6:
            with contextlib.redirect_stderr(io.StringIO()) as stderr_f6:
                term_logger.success("testytest")
        stdout = stdout_f6.getvalue()
        stderr = stderr_f6.getvalue()
        self.assertEqual(stdout, "")
        self.assertEqual(stderr, "")

    def test_log_level_3(self):
        term_logger = wpsync.log.TermLogger(3)
        with contextlib.redirect_stdout(io.StringIO()) as stdout_f1:
            with contextlib.redirect_stderr(io.StringIO()) as stderr_f1:
                term_logger.title("testytest")
        stdout = stdout_f1.getvalue()
        stderr = stderr_f1.getvalue()
        self.assertEqual(stdout, "")
        self.assertEqual(stderr, "")
        with contextlib.redirect_stdout(io.StringIO()) as stdout_f2:
            with contextlib.redirect_stderr(io.StringIO()) as stderr_f2:
                term_logger.step("testytest")
        stdout = stdout_f2.getvalue()
        stderr = stderr_f2.getvalue()
        self.assertEqual(stdout, "")
        self.assertEqual(stderr, "")
        with contextlib.redirect_stdout(io.StringIO()) as stdout_f3:
            with contextlib.redirect_stderr(io.StringIO()) as stderr_f3:
                term_logger.error("testytest")
        stdout = stdout_f3.getvalue()
        stderr = stderr_f3.getvalue()
        self.assertEqual(stdout, "")
        self.assertEqual(stderr, "✗ testytest\n")
        with contextlib.redirect_stdout(io.StringIO()) as stdout_f4:
            with contextlib.redirect_stderr(io.StringIO()) as stderr_f4:
                term_logger.warning("testytest")
        stdout = stdout_f4.getvalue()
        stderr = stderr_f4.getvalue()
        self.assertEqual(stdout, "")
        self.assertEqual(stderr, "⚠ testytest\n")
        with contextlib.redirect_stdout(io.StringIO()) as stdout_f5:
            with contextlib.redirect_stderr(io.StringIO()) as stderr_f5:
                term_logger.info("testytest")
        stdout = stdout_f5.getvalue()
        stderr = stderr_f5.getvalue()
        self.assertEqual(stdout, "ℹ testytest\n")
        self.assertEqual(stderr, "")
        with contextlib.redirect_stdout(io.StringIO()) as stdout_f6:
            with contextlib.redirect_stderr(io.StringIO()) as stderr_f6:
                term_logger.success("testytest")
        stdout = stdout_f6.getvalue()
        stderr = stderr_f6.getvalue()
        self.assertEqual(stdout, "")
        self.assertEqual(stderr, "")

    def test_log_level_4(self):
        term_logger = wpsync.log.TermLogger(4)
        with contextlib.redirect_stdout(io.StringIO()) as stdout_f1:
            with contextlib.redirect_stderr(io.StringIO()) as stderr_f1:
                term_logger.title("testytest")
        stdout = stdout_f1.getvalue()
        stderr = stderr_f1.getvalue()
        self.assertEqual(stdout, "➙ testytest\n")
        self.assertEqual(stderr, "")
        with contextlib.redirect_stdout(io.StringIO()) as stdout_f2:
            with contextlib.redirect_stderr(io.StringIO()) as stderr_f2:
                term_logger.step("testytest")
        stdout = stdout_f2.getvalue()
        stderr = stderr_f2.getvalue()
        self.assertEqual(stdout, "• testytest\n")
        self.assertEqual(stderr, "")
        with contextlib.redirect_stdout(io.StringIO()) as stdout_f3:
            with contextlib.redirect_stderr(io.StringIO()) as stderr_f3:
                term_logger.error("testytest")
        stdout = stdout_f3.getvalue()
        stderr = stderr_f3.getvalue()
        self.assertEqual(stdout, "")
        self.assertEqual(stderr, "✗ testytest\n")
        with contextlib.redirect_stdout(io.StringIO()) as stdout_f4:
            with contextlib.redirect_stderr(io.StringIO()) as stderr_f4:
                term_logger.warning("testytest")
        stdout = stdout_f4.getvalue()
        stderr = stderr_f4.getvalue()
        self.assertEqual(stdout, "")
        self.assertEqual(stderr, "⚠ testytest\n")
        with contextlib.redirect_stdout(io.StringIO()) as stdout_f5:
            with contextlib.redirect_stderr(io.StringIO()) as stderr_f5:
                term_logger.info("testytest")
        stdout = stdout_f5.getvalue()
        stderr = stderr_f5.getvalue()
        self.assertEqual(stdout, "ℹ testytest\n")
        self.assertEqual(stderr, "")
        with contextlib.redirect_stdout(io.StringIO()) as stdout_f6:
            with contextlib.redirect_stderr(io.StringIO()) as stderr_f6:
                term_logger.success("testytest")
        stdout = stdout_f6.getvalue()
        stderr = stderr_f6.getvalue()
        self.assertEqual(stdout, "✔ testytest\n")
        self.assertEqual(stderr, "")


class TestFileLogger(TestLogger):
    def test_title(self):
        tmp_file = tempfile.NamedTemporaryFile()
        file_logger = wpsync.log.FileLogger(tmp_file.name, 4)
        file_logger.title("testytest")
        tmp_file.seek(0)
        tmp_content = tmp_file.read().decode("utf-8")
        self.assertRegex(tmp_content, r"^\[.*?\] -> testytest\s$")
        tmp_file.close()

    def test_step(self):
        tmp_file = tempfile.NamedTemporaryFile()
        file_logger = wpsync.log.FileLogger(tmp_file.name, 4)
        file_logger.step("testytest")
        tmp_file.seek(0)
        tmp_content = tmp_file.read().decode("utf-8")
        self.assertRegex(tmp_content, r"^\[.*?\]  - testytest\s$")
        tmp_file.close()

    def test_error(self):
        tmp_file = tempfile.NamedTemporaryFile()
        file_logger = wpsync.log.FileLogger(tmp_file.name, 4)
        file_logger.error("testytest")
        tmp_file.seek(0)
        tmp_content = tmp_file.read().decode("utf-8")
        self.assertRegex(tmp_content, r"^\[.*?\]  x testytest\s$")
        tmp_file.close()

    def test_warning(self):
        tmp_file = tempfile.NamedTemporaryFile()
        file_logger = wpsync.log.FileLogger(tmp_file.name, 4)
        file_logger.warning("testytest")
        tmp_file.seek(0)
        tmp_content = tmp_file.read().decode("utf-8")
        self.assertRegex(tmp_content, r"^\[.*?\]  ! testytest\s$")
        tmp_file.close()

    def test_info(self):
        tmp_file = tempfile.NamedTemporaryFile()
        file_logger = wpsync.log.FileLogger(tmp_file.name, 4)
        file_logger.info("testytest")
        tmp_file.seek(0)
        tmp_content = tmp_file.read().decode("utf-8")
        self.assertRegex(tmp_content, r"^\[.*?\]  i testytest\s$")
        tmp_file.close()

    def test_success(self):
        tmp_file = tempfile.NamedTemporaryFile()
        file_logger = wpsync.log.FileLogger(tmp_file.name, 4)
        file_logger.success("testytest")
        tmp_file.seek(0)
        tmp_content = tmp_file.read().decode("utf-8")
        self.assertRegex(tmp_content, r"^\[.*?\]  \+ testytest\s$")
        tmp_file.close()

    def test_log_level_0(self):
        tmp_file = tempfile.NamedTemporaryFile()
        file_logger = wpsync.log.FileLogger(tmp_file.name, 0)
        file_logger.title("testytest")
        tmp_file.seek(0)
        tmp_content = tmp_file.read().decode("utf-8")
        self.assertRegex(tmp_content, r"^$")
        tmp_file.close()

        tmp_file = tempfile.NamedTemporaryFile()
        file_logger = wpsync.log.FileLogger(tmp_file.name, 0)
        file_logger.step("testytest")
        tmp_file.seek(0)
        tmp_content = tmp_file.read().decode("utf-8")
        self.assertRegex(tmp_content, r"^$")
        tmp_file.close()

        tmp_file = tempfile.NamedTemporaryFile()
        file_logger = wpsync.log.FileLogger(tmp_file.name, 0)
        file_logger.error("testytest")
        tmp_file.seek(0)
        tmp_content = tmp_file.read().decode("utf-8")
        self.assertRegex(tmp_content, r"^$")
        tmp_file.close()

        tmp_file = tempfile.NamedTemporaryFile()
        file_logger = wpsync.log.FileLogger(tmp_file.name, 0)
        file_logger.warning("testytest")
        tmp_file.seek(0)
        tmp_content = tmp_file.read().decode("utf-8")
        self.assertRegex(tmp_content, r"^$")
        tmp_file.close()

        tmp_file = tempfile.NamedTemporaryFile()
        file_logger = wpsync.log.FileLogger(tmp_file.name, 0)
        file_logger.info("testytest")
        tmp_file.seek(0)
        tmp_content = tmp_file.read().decode("utf-8")
        self.assertRegex(tmp_content, r"^$")
        tmp_file.close()

        tmp_file = tempfile.NamedTemporaryFile()
        file_logger = wpsync.log.FileLogger(tmp_file.name, 0)
        file_logger.success("testytest")
        tmp_file.seek(0)
        tmp_content = tmp_file.read().decode("utf-8")
        self.assertRegex(tmp_content, r"^$")
        tmp_file.close()

    def test_log_level_1(self):
        tmp_file = tempfile.NamedTemporaryFile()
        file_logger = wpsync.log.FileLogger(tmp_file.name, 1)
        file_logger.title("testytest")
        tmp_file.seek(0)
        tmp_content = tmp_file.read().decode("utf-8")
        self.assertRegex(tmp_content, r"^$")
        tmp_file.close()

        tmp_file = tempfile.NamedTemporaryFile()
        file_logger = wpsync.log.FileLogger(tmp_file.name, 1)
        file_logger.step("testytest")
        tmp_file.seek(0)
        tmp_content = tmp_file.read().decode("utf-8")
        self.assertRegex(tmp_content, r"^$")
        tmp_file.close()

        tmp_file = tempfile.NamedTemporaryFile()
        file_logger = wpsync.log.FileLogger(tmp_file.name, 1)
        file_logger.error("testytest")
        tmp_file.seek(0)
        tmp_content = tmp_file.read().decode("utf-8")
        self.assertRegex(tmp_content, r"^\[.*?\]  x testytest\s$")
        tmp_file.close()

        tmp_file = tempfile.NamedTemporaryFile()
        file_logger = wpsync.log.FileLogger(tmp_file.name, 1)
        file_logger.warning("testytest")
        tmp_file.seek(0)
        tmp_content = tmp_file.read().decode("utf-8")
        self.assertRegex(tmp_content, r"^$")
        tmp_file.close()

        tmp_file = tempfile.NamedTemporaryFile()
        file_logger = wpsync.log.FileLogger(tmp_file.name, 1)
        file_logger.info("testytest")
        tmp_file.seek(0)
        tmp_content = tmp_file.read().decode("utf-8")
        self.assertRegex(tmp_content, r"^$")
        tmp_file.close()

        tmp_file = tempfile.NamedTemporaryFile()
        file_logger = wpsync.log.FileLogger(tmp_file.name, 1)
        file_logger.success("testytest")
        tmp_file.seek(0)
        tmp_content = tmp_file.read().decode("utf-8")
        self.assertRegex(tmp_content, r"^$")
        tmp_file.close()

    def test_log_level_2(self):
        tmp_file = tempfile.NamedTemporaryFile()
        file_logger = wpsync.log.FileLogger(tmp_file.name, 2)
        file_logger.title("testytest")
        tmp_file.seek(0)
        tmp_content = tmp_file.read().decode("utf-8")
        self.assertRegex(tmp_content, r"^$")
        tmp_file.close()

        tmp_file = tempfile.NamedTemporaryFile()
        file_logger = wpsync.log.FileLogger(tmp_file.name, 2)
        file_logger.step("testytest")
        tmp_file.seek(0)
        tmp_content = tmp_file.read().decode("utf-8")
        self.assertRegex(tmp_content, r"^$")
        tmp_file.close()

        tmp_file = tempfile.NamedTemporaryFile()
        file_logger = wpsync.log.FileLogger(tmp_file.name, 2)
        file_logger.error("testytest")
        tmp_file.seek(0)
        tmp_content = tmp_file.read().decode("utf-8")
        self.assertRegex(tmp_content, r"^\[.*?\]  x testytest\s$")
        tmp_file.close()

        tmp_file = tempfile.NamedTemporaryFile()
        file_logger = wpsync.log.FileLogger(tmp_file.name, 2)
        file_logger.warning("testytest")
        tmp_file.seek(0)
        tmp_content = tmp_file.read().decode("utf-8")
        self.assertRegex(tmp_content, r"^\[.*?\]  ! testytest\s$")
        tmp_file.close()

        tmp_file = tempfile.NamedTemporaryFile()
        file_logger = wpsync.log.FileLogger(tmp_file.name, 2)
        file_logger.info("testytest")
        tmp_file.seek(0)
        tmp_content = tmp_file.read().decode("utf-8")
        self.assertRegex(tmp_content, r"^$")
        tmp_file.close()

        tmp_file = tempfile.NamedTemporaryFile()
        file_logger = wpsync.log.FileLogger(tmp_file.name, 2)
        file_logger.success("testytest")
        tmp_file.seek(0)
        tmp_content = tmp_file.read().decode("utf-8")
        self.assertRegex(tmp_content, r"^$")
        tmp_file.close()

    def test_log_level_3(self):
        tmp_file = tempfile.NamedTemporaryFile()
        file_logger = wpsync.log.FileLogger(tmp_file.name, 3)
        file_logger.title("testytest")
        tmp_file.seek(0)
        tmp_content = tmp_file.read().decode("utf-8")
        self.assertRegex(tmp_content, r"^$")
        tmp_file.close()

        tmp_file = tempfile.NamedTemporaryFile()
        file_logger = wpsync.log.FileLogger(tmp_file.name, 3)
        file_logger.step("testytest")
        tmp_file.seek(0)
        tmp_content = tmp_file.read().decode("utf-8")
        self.assertRegex(tmp_content, r"^$")
        tmp_file.close()

        tmp_file = tempfile.NamedTemporaryFile()
        file_logger = wpsync.log.FileLogger(tmp_file.name, 3)
        file_logger.error("testytest")
        tmp_file.seek(0)
        tmp_content = tmp_file.read().decode("utf-8")
        self.assertRegex(tmp_content, r"^\[.*?\]  x testytest\s$")
        tmp_file.close()

        tmp_file = tempfile.NamedTemporaryFile()
        file_logger = wpsync.log.FileLogger(tmp_file.name, 3)
        file_logger.warning("testytest")
        tmp_file.seek(0)
        tmp_content = tmp_file.read().decode("utf-8")
        self.assertRegex(tmp_content, r"^\[.*?\]  ! testytest\s$")
        tmp_file.close()

        tmp_file = tempfile.NamedTemporaryFile()
        file_logger = wpsync.log.FileLogger(tmp_file.name, 3)
        file_logger.info("testytest")
        tmp_file.seek(0)
        tmp_content = tmp_file.read().decode("utf-8")
        self.assertRegex(tmp_content, r"^\[.*?\]  i testytest\s$")
        tmp_file.close()

        tmp_file = tempfile.NamedTemporaryFile()
        file_logger = wpsync.log.FileLogger(tmp_file.name, 3)
        file_logger.success("testytest")
        tmp_file.seek(0)
        tmp_content = tmp_file.read().decode("utf-8")
        self.assertRegex(tmp_content, r"^$")
        tmp_file.close()

    def test_log_level_4(self):
        tmp_file = tempfile.NamedTemporaryFile()
        file_logger = wpsync.log.FileLogger(tmp_file.name, 4)
        file_logger.title("testytest")
        tmp_file.seek(0)
        tmp_content = tmp_file.read().decode("utf-8")
        self.assertRegex(tmp_content, r"^\[.*?\] -> testytest\s$")
        tmp_file.close()

        tmp_file = tempfile.NamedTemporaryFile()
        file_logger = wpsync.log.FileLogger(tmp_file.name, 4)
        file_logger.step("testytest")
        tmp_file.seek(0)
        tmp_content = tmp_file.read().decode("utf-8")
        self.assertRegex(tmp_content, r"^\[.*?\]  - testytest\s$")
        tmp_file.close()

        tmp_file = tempfile.NamedTemporaryFile()
        file_logger = wpsync.log.FileLogger(tmp_file.name, 4)
        file_logger.error("testytest")
        tmp_file.seek(0)
        tmp_content = tmp_file.read().decode("utf-8")
        self.assertRegex(tmp_content, r"^\[.*?\]  x testytest\s$")
        tmp_file.close()

        tmp_file = tempfile.NamedTemporaryFile()
        file_logger = wpsync.log.FileLogger(tmp_file.name, 4)
        file_logger.warning("testytest")
        tmp_file.seek(0)
        tmp_content = tmp_file.read().decode("utf-8")
        self.assertRegex(tmp_content, r"^\[.*?\]  ! testytest\s$")
        tmp_file.close()

        tmp_file = tempfile.NamedTemporaryFile()
        file_logger = wpsync.log.FileLogger(tmp_file.name, 4)
        file_logger.info("testytest")
        tmp_file.seek(0)
        tmp_content = tmp_file.read().decode("utf-8")
        self.assertRegex(tmp_content, r"^\[.*?\]  i testytest\s$")
        tmp_file.close()

        tmp_file = tempfile.NamedTemporaryFile()
        file_logger = wpsync.log.FileLogger(tmp_file.name, 4)
        file_logger.success("testytest")
        tmp_file.seek(0)
        tmp_content = tmp_file.read().decode("utf-8")
        self.assertRegex(tmp_content, r"^\[.*?\]  \+ testytest\s$")
        tmp_file.close()
