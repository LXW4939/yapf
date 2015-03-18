# Copyright 2015 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Tests for yapf.blank_line_calculator."""

import sys
import textwrap
import unittest

from yapf.yapflib import blank_line_calculator
from yapf.yapflib import comment_splicer
from yapf.yapflib import pytree_unwrapper
from yapf.yapflib import pytree_utils
from yapf.yapflib import pytree_visitor
from yapf.yapflib import reformatter
from yapf.yapflib import split_penalty
from yapf.yapflib import subtype_assigner


class BlankLineCalculatorTest(unittest.TestCase):

  def testDecorators(self):
    unformatted_code = textwrap.dedent("""\
        @bork()

        def foo():
          pass
        """)
    expected_formatted_code = textwrap.dedent("""\
        @bork()
        def foo():
          pass
        """)
    uwlines = _ParseAndUnwrap(unformatted_code)
    self.assertEqual(expected_formatted_code, reformatter.Reformat(uwlines))

  def testComplexDecorators(self):
    unformatted_code = textwrap.dedent("""\
        import sys
        @bork()

        def foo():
          pass
        @fork()

        class moo(object):
          @bar()
          @baz()

          def method(self):
            pass
        """)
    expected_formatted_code = textwrap.dedent("""\
        import sys


        @bork()
        def foo():
          pass


        @fork()
        class moo(object):

          @bar()
          @baz()
          def method(self):
            pass
        """)
    uwlines = _ParseAndUnwrap(unformatted_code)
    self.assertEqual(expected_formatted_code, reformatter.Reformat(uwlines))

  def testCodeAfterFunctionsAndClasses(self):
    unformatted_code = textwrap.dedent("""\
        def foo():
          pass
        top_level_code = True
        class moo(object):
          def method_1(self):
            pass
          ivar_a = 42
          ivar_b = 13
          def method_2(self):
            pass
        try:
          raise Error
        except Error as error:
          pass
        """)
    expected_formatted_code = textwrap.dedent("""\
        def foo():
          pass


        top_level_code = True


        class moo(object):

          def method_1(self):
            pass

          ivar_a = 42
          ivar_b = 13

          def method_2(self):
            pass


        try:
          raise Error
        except Error as error:
          pass
        """)
    uwlines = _ParseAndUnwrap(unformatted_code)
    self.assertEqual(expected_formatted_code, reformatter.Reformat(uwlines))

  def testCommentSpacing(self):
    unformatted_code = textwrap.dedent("""\
        # This is the first comment
        # And it's multiline

        # This is the second comment

        def foo():
          pass

        # multiline before a
        # class definition

        # This is the second comment

        class qux(object):
          pass


        # An attached comment.
        class bar(object):
          '''class docstring'''
          # Comment attached to
          # function
          def foo(self):
            '''Another docstring.'''
            # Another multiline
            # comment
            pass
        """)
    expected_formatted_code = textwrap.dedent("""\
        # This is the first comment
        # And it's multiline

        # This is the second comment


        def foo():
          pass

        # multiline before a
        # class definition

        # This is the second comment


        class qux(object):
          pass


        # An attached comment.
        class bar(object):
          '''class docstring'''

          # Comment attached to
          # function
          def foo(self):
            '''Another docstring.'''
            # Another multiline
            # comment
            pass
        """)
    uwlines = _ParseAndUnwrap(unformatted_code)
    self.assertEqual(expected_formatted_code, reformatter.Reformat(uwlines))

  def testCommentBeforeMethod(self):
    code = textwrap.dedent("""\
        class foo(object):

          # pylint: disable=invalid-name
          def f(self):
            pass
        """)
    uwlines = _ParseAndUnwrap(code)
    self.assertEqual(code, reformatter.Reformat(uwlines))

  def testCommentsBeforeClassDefs(self):
    code = textwrap.dedent('''\
        """Test."""

        # Comment


        class Foo(object):
          pass
        ''')
    uwlines = _ParseAndUnwrap(code)
    self.assertEqual(code, reformatter.Reformat(uwlines))

  def testComemntsBeforeDecorator(self):
    code = textwrap.dedent("""\
        # The @foo operator adds bork to a().
        @foo()
        def a():
          pass
        """)
    uwlines = _ParseAndUnwrap(code)
    self.assertEqual(code, reformatter.Reformat(uwlines))

    code = textwrap.dedent("""\
        # Hello world


        @foo()
        def a():
          pass
        """)
    uwlines = _ParseAndUnwrap(code)
    self.assertEqual(code, reformatter.Reformat(uwlines))


def _ParseAndUnwrap(code, dumptree=False):
  """Produces unwrapped lines from the given code.

  Parses the code into a tree, performs comment splicing and runs the
  unwrapper.

  Arguments:
    code: code to parse as a string
    dumptree: if True, the parsed pytree (after comment splicing) is dumped
      to stderr. Useful for debugging.

  Returns:
    List of unwrapped lines.
  """
  tree = pytree_utils.ParseCodeToTree(code)
  comment_splicer.SpliceComments(tree)
  subtype_assigner.AssignSubtypes(tree)
  split_penalty.ComputeSplitPenalties(tree)
  blank_line_calculator.CalculateBlankLines(tree)

  if dumptree:
    pytree_visitor.DumpPyTree(tree, target_stream=sys.stderr)

  uwlines = pytree_unwrapper.UnwrapPyTree(tree)
  for uwl in uwlines:
    uwl.CalculateFormattingInformation()

  return uwlines


def suite():
  result = unittest.TestSuite()
  result.addTests(unittest.makeSuite(BlankLineCalculatorTest))
  return result


if __name__ == '__main__':
  unittest.main()
