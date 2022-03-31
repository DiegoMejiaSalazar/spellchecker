class IntersercetedWord:
    def __init__(self, text, x0, top, y0, bottom, has_errors, suggestions):
        self.x0 = x0
        self.top = top
        self.y0 = y0
        self.bottom = bottom
        self.text = text
        self.has_errors = has_errors
        self.suggestions = suggestions
