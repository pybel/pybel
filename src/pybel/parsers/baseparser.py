import logging
from abc import abstractmethod

log = logging.getLogger(__name__)


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
        return self.get_language().parseString(s)

    @abstractmethod
    def get_language(self):
        """Gets the language represented by this parser"""
        pass
