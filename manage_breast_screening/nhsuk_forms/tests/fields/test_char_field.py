import pytest
from django.forms import Form, ValidationError
from django.forms.widgets import TelInput, Textarea, TextInput
from pytest_django.asserts import assertHTMLEqual

from ...fields import CharField


class TestCharField:
    @pytest.fixture
    def form_class(self):
        class TestForm(Form):
            field = CharField(
                label="Abc", initial="somevalue", max_length=10, max_words=None
            )
            field_with_visually_hidden_label = CharField(
                label="Abc",
                initial="somevalue",
                label_classes="nhsuk-u-visually-hidden",
            )
            field_with_visually_hidden_label_prefix = CharField(
                label="Abc",
                initial="somevalue",
                visually_hidden_label_prefix="some prefix: ",
            )
            field_with_visually_hidden_label_suffix = CharField(
                label="Abc",
                initial="somevalue",
                visually_hidden_label_suffix=": some suffix",
            )
            field_with_hint = CharField(
                label="With hint", initial="", hint="ALL UPPERCASE"
            )
            field_with_classes = CharField(
                label="With classes", initial="", classes="nhsuk-u-width-two-thirds"
            )
            field_with_extra_attrs = CharField(
                label="Extra",
                widget=TextInput(
                    attrs=dict(
                        autocomplete="off",
                        inputmode="numeric",
                        spellcheck="false",
                        autocapitalize="none",
                        pattern=r"\d{3}",
                    )
                ),
            )
            telephone_field = CharField(label="Ring ring", widget=TelInput)
            textfield = CharField(
                label="Text",
                widget=Textarea(
                    attrs={
                        "rows": "3",
                        "autocomplete": "autocomplete",
                        "spellcheck": "true",
                    }
                ),
                max_words=None,
            )
            textfield_simple = CharField(label="Text", widget=Textarea, max_words=None)
            char_count = CharField(
                label="Text",
                widget=Textarea,
                max_length=10,
                max_words=None,
            )
            char_count_max_words = CharField(label="Text", widget=Textarea, max_words=5)
            inputmode = CharField(label="Inputmode", inputmode="numeric")

        return TestForm

    def test_renders_nhs_input(self, form_class):
        assertHTMLEqual(
            form_class()["field"].as_field_group(),
            """
            <div class="nhsuk-form-group">
                <label class="nhsuk-label" for="id_field">
                    Abc
                </label><input class="nhsuk-input" id="id_field" name="field" type="text" value="somevalue">
            </div>
            """,
        )

    def test_renders_nhs_input_with_visually_hidden_label(self, form_class):
        assertHTMLEqual(
            form_class()["field_with_visually_hidden_label"].as_field_group(),
            """
            <div class="nhsuk-form-group">
                <label class="nhsuk-label nhsuk-u-visually-hidden" for="id_field_with_visually_hidden_label">
                    Abc
                </label><input class="nhsuk-input" id="id_field_with_visually_hidden_label" name="field_with_visually_hidden_label" type="text" value="somevalue">
            </div>
            """,
        )

    def test_renders_nhs_input_with_visually_hidden_label_prefix(self, form_class):
        assertHTMLEqual(
            form_class()["field_with_visually_hidden_label_prefix"].as_field_group(),
            """
            <div class="nhsuk-form-group">
                <label class="nhsuk-label" for="id_field_with_visually_hidden_label_prefix">
                    <span class="nhsuk-u-visually-hidden">some prefix: </span>Abc
                </label><input class="nhsuk-input" id="id_field_with_visually_hidden_label_prefix" name="field_with_visually_hidden_label_prefix" type="text" value="somevalue">
            </div>
            """,
        )

    def test_renders_nhs_input_with_visually_hidden_label_suffix(self, form_class):
        assertHTMLEqual(
            form_class()["field_with_visually_hidden_label_suffix"].as_field_group(),
            """
            <div class="nhsuk-form-group">
                <label class="nhsuk-label" for="id_field_with_visually_hidden_label_suffix">
                    Abc<span class="nhsuk-u-visually-hidden">: some suffix</span>
                </label><input class="nhsuk-input" id="id_field_with_visually_hidden_label_suffix" name="field_with_visually_hidden_label_suffix" type="text" value="somevalue">
            </div>
            """,
        )

    def test_renders_nhs_input_with_hint(self, form_class):
        assertHTMLEqual(
            form_class()["field_with_hint"].as_field_group(),
            """
            <div class="nhsuk-form-group">
                <label class="nhsuk-label" for="id_field_with_hint">
                    With hint
                </label>
                <div class="nhsuk-hint" id="id_field_with_hint-hint">ALL UPPERCASE</div>
                <input class="nhsuk-input" id="id_field_with_hint" name="field_with_hint" type="text" aria-describedby="id_field_with_hint-hint" value="">
            </div>
            """,
        )

    def test_renders_nhs_input_with_classes(self, form_class):
        assertHTMLEqual(
            form_class()["field_with_classes"].as_field_group(),
            """
            <div class="nhsuk-form-group">
                <label class="nhsuk-label" for="id_field_with_classes">
                    With classes
                </label>
                <input class="nhsuk-input nhsuk-u-width-two-thirds" id="id_field_with_classes" name="field_with_classes" type="text" value="">
            </div>
            """,
        )

    def test_renders_nhs_input_with_extra_attrs(self, form_class):
        assertHTMLEqual(
            form_class()["field_with_extra_attrs"].as_field_group(),
            """
            <div class="nhsuk-form-group">
                <label class="nhsuk-label" for="id_field_with_extra_attrs">
                    Extra
                </label>
                <input autocomplete="off" autocapitalize="none" spellcheck="false" inputmode="numeric" pattern="\\d{3}" class="nhsuk-input" id="id_field_with_extra_attrs" name="field_with_extra_attrs" type="text" value="">
            </div>
            """,
        )

    def test_bound_value_reflected_in_html_value(self, form_class):
        assertHTMLEqual(
            form_class({"field": "othervalue"})["field"].as_field_group(),
            """
            <div class="nhsuk-form-group">
                <label class="nhsuk-label" for="id_field">
                    Abc
                </label><input class="nhsuk-input" id="id_field" name="field" type="text" value="othervalue">
            </div>
            """,
        )

    def test_invalid_value_renders_validation_error(self, form_class):
        assertHTMLEqual(
            form_class({"field": "reallylongvalue"})["field"].as_field_group(),
            """
            <div class="nhsuk-form-group nhsuk-form-group--error">
                <label class="nhsuk-label" for="id_field">
                    Abc
                </label>
                <span class="nhsuk-error-message" id="id_field-error">
                <span class="nhsuk-u-visually-hidden">Error:</span> Ensure this value has at most 10 characters (it has 15).</span>
                <input class="nhsuk-input nhsuk-input--error" id="id_field" name="field" type="text" value="reallylongvalue" aria-describedby="id_field-error">
            </div>
            """,
        )

    def test_telinput_renders_input_with_type_tel(self, form_class):
        assertHTMLEqual(
            form_class()["telephone_field"].as_field_group(),
            """
            <div class="nhsuk-form-group">
                <label class="nhsuk-label" for="id_telephone_field">
                    Ring ring
                </label><input type="tel" class="nhsuk-input" id="id_telephone_field" name="telephone_field" value="">
            </div>
            """,
        )

    def test_textarea_renders_textarea(self, form_class):
        assertHTMLEqual(
            form_class()["textfield"].as_field_group(),
            """
                <div class="nhsuk-form-group">
                    <label class="nhsuk-label" for="id_textfield">
                        Text
                    </label>
                    <textarea class="nhsuk-textarea" id="id_textfield" name="textfield" rows="3" autocomplete="autocomplete" spellcheck="true"></textarea>
                </div>
                """,
        )

    def test_textarea_class_renders_textarea(self, form_class):
        assertHTMLEqual(
            form_class()["textfield_simple"].as_field_group(),
            """
                <div class="nhsuk-form-group">
                    <label class="nhsuk-label" for="id_textfield_simple">
                        Text
                    </label>
                    <textarea class="nhsuk-textarea" id="id_textfield_simple" name="textfield_simple" rows="10"></textarea>
                </div>
                """,
        )

    def test_textarea_with_max_length_renders_character_count(self, form_class):
        assertHTMLEqual(
            form_class()["char_count"].as_field_group(),
            """
            <div class="nhsuk-character-count nhsuk-form-group" data-maxlength="10" data-threshold="25" data-module="nhsuk-character-count">
                <label class="nhsuk-label" for="id_char_count">
                    Text
                </label>
                <textarea aria-describedby="id_char_count-info" class="nhsuk-js-character-count nhsuk-textarea" id="id_char_count" name="char_count" rows="10"></textarea>
                <div class="nhsuk-character-count__message nhsuk-hint" id="id_char_count-info">
                    You can enter up to 10 characters
                </div>
            </div>
            """,
        )

    def test_textarea_with_maxwords_renders_character_count(self, form_class):
        assertHTMLEqual(
            form_class()["char_count_max_words"].as_field_group(),
            """
            <div class="nhsuk-character-count nhsuk-form-group" data-maxwords="5" data-threshold="25" data-module="nhsuk-character-count">
                <label class="nhsuk-label" for="id_char_count_max_words">
                    Text
                </label>
                <textarea aria-describedby="id_char_count_max_words-info" class="nhsuk-js-character-count nhsuk-textarea" id="id_char_count_max_words" name="char_count_max_words" rows="10"></textarea>
                <div class="nhsuk-character-count__message nhsuk-hint" id="id_char_count_max_words-info">
                    You can enter up to 5 words
                </div>
            </div>
            """,
        )

    def test_max_word_validation(self):
        field = CharField(label="Text", widget=Textarea, max_words=5)

        with pytest.raises(ValidationError, match="Enter 5 words or less"):
            field.clean("one two three four five six")

    def test_renders_inputmode(self, form_class):
        assertHTMLEqual(
            form_class()["inputmode"].as_field_group(),
            """
            <div class="nhsuk-form-group">
                <label class="nhsuk-label" for="id_inputmode">
                    Inputmode
                </label><input class="nhsuk-input" id="id_inputmode" name="inputmode" type="text" inputmode="numeric" value="">
            </div>
            """,
        )
