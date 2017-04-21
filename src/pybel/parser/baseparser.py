# -*- coding: utf-8 -*-

import logging
import time

log = logging.getLogger(__name__)

__all__ = ['BaseParser']


class BaseParser:
    """This abstract class represents a language backed by a PyParsing statement

    Multiple parsers can be easily chained together when they are all inheriting from this base class
    """

    def __init__(self, language, streamline=False):
        self.language = language

        #: The parser can hold an internal state of the current line
        self.line_number = None

        if streamline:
            self.streamline()

    def parse_lines(self, lines):
        """Parses multiple lines in succession
        
        :return: An list of the resulting parsed lines' tokens
        :rtype: list
        """
        return [self.parseString(line) for line in lines]

    def parseString(self, line, line_number=None):
        """Parses a string with the language represented by this parser
        
        :param str line: A string representing an instance of this parser's language
        :param int line_number: The current line number of the parser
        """
        if line_number is None:
            return self.language.parseString(line)

        self.line_number = line_number
        result = self.language.parseString(line)
        self.line_number = None
        return result

    def streamline(self):
        """Streamlines the language represented by this parser to make queries run faster"""
        t = time.time()
        self.language.streamline()
        log.info('Finished streamlining %s in %.02fs', self.__class__.__name__, time.time() - t)
