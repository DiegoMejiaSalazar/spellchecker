class IntersercetedWord:
    def __init__(self, text, x0, top, y0, bottom, has_contextual_errors, has_ortographical_errors, suggestions):
        self.x0 = x0
        self.top = top
        self.y0 = y0
        self.bottom = bottom
        self.text = text
        self.is_contextual_error = has_contextual_errors
        self.is_ortographical_error = has_ortographical_errors
        self.suggestions = suggestions
        self.is_useless = False

    def show_coordinates(self):
        print(self.x0)
        print(self.top)
        print(self.y0)
        print(self.bottom)
