def sanitize_statement_lines(statement_lines):
    """
    Given a line
    :param statement_lines:
    :return:
    """
    new_lines = []
    statement_line_iter = iter(statement_lines)
    for line in statement_line_iter:

        # Group multi-line comments with slash delimiiters
        if line.startswith('SET Evidence') and (line.endswith('/') or line.endswith('\\')):

            next_line = next(statement_line_iter)

            while next_line.endswith('/') or next_line.endswith('\\'):
                line = '{} {}'.format(line[:-1].strip(), next_line)
                next_line = next(statement_line_iter)

            line = '{} {}'.format(line[:-1].strip(), next_line)

        # Group multi-line comments with forgotten delimiters
        elif line.startswith('SET Evidence') and not line.endswith('"'):
            next_line = next(statement_line_iter)

            while not next_line.endswith('"'):
                line = '{} {}'.format(line.strip(), next_line)
                next_line = next(statement_line_iter)

            line = '{} {}'.format(line, next_line)

        new_lines.append(line)
    return new_lines
