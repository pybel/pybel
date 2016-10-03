import logging
from abc import abstractmethod
from time import time
from pyparsing import Suppress, ZeroOrMore, White, dblQuotedString, removeQuotes, Word, alphanums

log = logging.getLogger(__name__)

W = Suppress(ZeroOrMore(White()))
WCW = W + Suppress(',') + W
LP = Suppress('(') + W
RP = W + Suppress(')')

word = Word(alphanums)
quote = dblQuotedString().setParseAction(removeQuotes)


class BaseParser:
    """This abstract class represents a language backed by a PyParsing statement

    Multiple parsers can be easily chained together when they are all inheriting from this base class
    """

    def parse_lines(self, l):
        """Parses multiple lines successively"""
        return [self.parse(line) for line in l]

    def parse(self, s):
        """Parses a string with the language represented by this parser
        :param s: input string
        :type s: str
        """
        result = self.get_language().parseString(s)
        return result

    @abstractmethod
    def get_language(self):
        """Gets the language represented by this parser"""
        return
