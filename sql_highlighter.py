import re

from PySide2.QtCore import (Qt, QRegExp)
from PySide2.QtGui import (QColor, QFont,
                           QSyntaxHighlighter, QTextCharFormat)


class SQLHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super(SQLHighlighter, self).__init__(parent)

        self.highlight_rules = []

        # SQL keyword format
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor(113, 171, 255))  # Dark gray color for keywords
        keyword_format.setFontWeight(QFont.Bold)
        keyword_format.setFont(QFont("MesloLGS NF", 11))
        keywords = [
            "SELECT", "DISTINCT", "FROM", "WHERE", "GROUP BY", "HAVING", "ORDER BY", "INSERT INTO", "VALUES", "UPDATE",
            "SET", "DELETE FROM", "LIMIT", "JOIN", "LEFT JOIN", "RIGHT JOIN", "INNER JOIN", "ON", "AND", "OR", "NOT",
            "NULL", "TRUE", "FALSE"
        ]
        for word in keywords:
            pattern = "\\b" + word + "\\b"
            rule = (pattern, keyword_format)
            self.highlight_rules.append(rule)

        # Function format
        function_format = QTextCharFormat()
        function_format.setForeground(QColor(0, 120, 190))  # Blue color for functions
        function_format.setFont(QFont("MesloLGS NF", 11, QFont.Normal))
        functions = [
            "COUNT", "SUM", "AVG", "MIN", "MAX", "IF", "CASE", "WHEN", "THEN", "ELSE",
            "CONCAT", "SUBSTRING", "UPPER", "LOWER", "TRIM"
        ]
        for func in functions:
            pattern = "\\b" + func + "\\b"
            rule = (pattern, function_format)
            self.highlight_rules.append(rule)

        # Operator format
        operator_format = QTextCharFormat()
        operator_format.setForeground(QColor(255, 149, 0))  # Orange color for operators
        operator_format.setFont(QFont("MesloLGS NF", 11, QFont.Normal))
        operators = ["=", "<", ">", "<=", ">=", "!=", "<>", "AND", "OR", "NOT", "BETWEEN", "IN", "LIKE", "IS NULL",
                     "IS NOT NULL"]
        for op in operators:
            pattern = "\\b" + re.escape(op) + "\\b"
            rule = (pattern, operator_format)
            self.highlight_rules.append(rule)

        # Table and field format (e.g., tableName.fieldName)
        table_field_format = QTextCharFormat()
        table_field_format.setForeground(QColor(150, 150, 150))  # Light gray color for tables and fields
        table_field_format.setFont(QFont("MesloLGS NF", 11, QFont.Normal))
        rule = (r"\b\w+\.\w+\b", table_field_format)
        self.highlight_rules.append(rule)

        # Multi-line comment format (/* ... */)
        multi_line_comment_format = QTextCharFormat()
        multi_line_comment_format.setForeground(QColor(116, 116, 116))
        multi_line_comment_format.setFontItalic(True)
        multi_line_comment_format.setFont(QFont("MesloLGS NF", 11))
        rule = (r"/\*.*\*/", multi_line_comment_format)
        self.highlight_rules.append(rule)

        # Variable/parameter format (e.g., :variable_name)
        variable_format = QTextCharFormat()
        variable_format.setForeground(QColor(230, 126, 34))  # Dark orange color for variables
        variable_format.setFont(QFont("MesloLGS NF", 11, QFont.Normal))
        rule = (r":\w+", variable_format)
        self.highlight_rules.append(rule)

        # Quoted identifier format (e.g., "NblsSupplementaryAgreement")
        identifier_format = QTextCharFormat()
        identifier_format.setForeground(QColor(249, 168, 37))  # Dark green color for identifiers
        identifier_format.setFont(QFont("MesloLGS NF", 11, QFont.Normal))
        rule = (r'"[^"]*"', identifier_format)
        self.highlight_rules.append(rule)

        # String format
        string_format = QTextCharFormat()
        string_format.setForeground(QColor(213, 99, 88))  # Green color for strings
        string_format.setFont(QFont("MesloLGS NF", 11, QFont.Normal))
        rule = (r"'.*?'", string_format)
        self.highlight_rules.append(rule)

        # Comment format
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor(116, 116, 116))  # Dark gray color for comments
        comment_format.setFontItalic(True)
        comment_format.setFont(QFont("MesloLGS NF", 11))
        rule = (r"--[^\n]*", comment_format)
        self.highlight_rules.append(rule)

        # Numeric format
        numeric_format = QTextCharFormat()
        numeric_format.setForeground(QColor(187, 35, 0))  # Red color for numbers
        numeric_format.setFont(QFont("MesloLGS NF", 11))
        rule = (r"\b\d+\b", numeric_format)
        self.highlight_rules.append(rule)

    def highlightBlock(self, text):
        for pattern, char_format in self.highlight_rules:
            expression = QRegExp(pattern, Qt.CaseInsensitive)
            index = expression.indexIn(text)
            while index >= 0:
                length = expression.matchedLength()
                self.setFormat(index, length, char_format)
                index = expression.indexIn(text, index + length)
