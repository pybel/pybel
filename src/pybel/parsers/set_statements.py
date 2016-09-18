from .utils import subitergroup, parse_list


def sanitize_statement_lines(statement_lines):
    """
    Group multi-lines with breaks and forgotten delimiters
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


def parse_commands(sanitary_statement_lines):
    """
    Parse out commands
    :param sanitary_statement_lines:
    :return:
    """
    line_cmds = []
    for line in sanitary_statement_lines:
        if line.startswith('SET'):
            line = line.strip('SET').strip()
            line = [x.strip() for x in line.split('=', 1)]
            command, value = line

            if command == 'Evidence':
                value = handle_evidence(value)

            line_cmds.append(('S', command, value))

        elif line.startswith('UNSET'):
            line = line.strip('UNSET').strip()
            line_cmds.append(('U', line))
        else:
            line_cmds.append(('X', line))
    return line_cmds


def handle_evidence(s):
    return s.strip('"')


def handle_citation(s):
    q = parse_list(s)

    if len(q) == 3:
        return dict(zip(['source', 'citation', 'id'], q))
    elif len(q) == 6:
        return dict(zip(['source', 'title', 'journal', 'date', 'authors', 'id'], q))
    else:
        raise Exception('Dont know how to parse')


def group_statements(parsed_commands):
    """

    :param parsed_commands:
    :return:
    """
    res = []
    for command_line, subcommand_lines in subitergroup(parsed_commands, lambda t: t[0] == 'S' and t[1] == 'Citation'):
        tag, command, value = command_line
        citation = handle_citation(value)

        res.append({
            'citation': citation,
            'notes': subcommand_lines#list(z[1:] for z in subcommand_lines)
        })

    return res
