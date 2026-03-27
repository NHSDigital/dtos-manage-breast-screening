from unittest.mock import MagicMock, patch

import dmt
from dmt import PullRequest, format_pr_choice_label, select_prs


def make_pr(**kwargs):
    defaults = {
        "number": 1234,
        "title": "bump django from 4.2 to 5.0",
        "check_status": "✓ Passing",
        "review_decision": "✓ Approved",
        "mergeable_display": "✓ Mergeable",
        "can_merge": True,
    }
    return PullRequest(**{**defaults, **kwargs})


# --- format_pr_choice_label ---


def test_pr_number_column_is_8_chars_wide():
    label = format_pr_choice_label(make_pr(number=1))
    assert label[:8] == "#1      "


def test_six_digit_pr_number_fits_in_8_char_column():
    label = format_pr_choice_label(make_pr(number=123456))
    assert label[:8] == "#123456 "


def test_title_short_padded_to_60_chars():
    label = format_pr_choice_label(make_pr(title="short"))
    title_col = label[8:68]
    assert title_col == "short".ljust(60)


def test_title_exactly_60_chars_not_truncated():
    title = "x" * 60
    label = format_pr_choice_label(make_pr(title=title))
    title_col = label[8:68]
    assert title_col == title


def test_title_over_60_chars_truncated_with_ellipsis():
    label = format_pr_choice_label(make_pr(title="x" * 61))
    title_col = label[8:68]
    assert len(title_col) == 60
    assert title_col == "x" * 59 + "…"


def test_title_truncation_boundary_at_exactly_61_chars():
    label_61 = format_pr_choice_label(make_pr(title="a" * 61))
    label_60 = format_pr_choice_label(make_pr(title="a" * 60))
    assert label_61[8:68] == "a" * 59 + "…"
    assert label_60[8:68] == "a" * 60


def test_columns_appear_in_order():
    pr = make_pr(
        check_status="✓ Passing",
        review_decision="✓ Approved",
        mergeable_display="✓ Mergeable",
    )
    label = format_pr_choice_label(pr)
    checks_pos = label.index("✓ Passing")
    review_pos = label.index("✓ Approved")
    mergeable_pos = label.index("✓ Mergeable")
    assert checks_pos < review_pos < mergeable_pos


# --- select_prs ---


def test_select_prs_returns_none_when_ask_returns_none():
    prs = [make_pr(number=1)]
    with patch("dmt.questionary") as mock_q:
        mock_q.Choice = MagicMock()
        mock_q.checkbox.return_value.ask.return_value = None
        result = select_prs(prs)
    assert result is None


def test_select_prs_returns_empty_list_when_no_selection():
    prs = [make_pr(number=1)]
    with patch("dmt.questionary") as mock_q:
        mock_q.Choice = MagicMock()
        mock_q.checkbox.return_value.ask.return_value = []
        result = select_prs(prs)
    assert result == []


def test_select_prs_returns_selected_pr_numbers():
    prs = [make_pr(number=1), make_pr(number=2)]
    with patch("dmt.questionary") as mock_q:
        mock_q.Choice = MagicMock()
        mock_q.checkbox.return_value.ask.return_value = [1, 2]
        result = select_prs(prs)
    assert result == [1, 2]


def test_select_prs_creates_one_choice_per_pr():
    prs = [make_pr(number=1), make_pr(number=2), make_pr(number=3)]
    with patch("dmt.questionary") as mock_q:
        mock_q.Choice = MagicMock(side_effect=lambda title, value: (title, value))
        mock_q.checkbox.return_value.ask.return_value = []
        select_prs(prs)
    assert mock_q.checkbox.call_count == 1
    assert mock_q.Choice.call_count == 3


def test_select_prs_passes_correct_label_and_value_to_choice():
    pr = make_pr(number=42)
    expected_label = format_pr_choice_label(pr)
    with patch("dmt.questionary") as mock_q:
        mock_q.Choice = MagicMock()
        mock_q.checkbox.return_value.ask.return_value = []
        select_prs([pr])
    mock_q.Choice.assert_called_once_with(title=expected_label, value=42)


# --- main() cancellation paths ---


def test_main_aborted_when_select_prs_returns_none(capsys):
    with patch("sys.argv", ["dmt"]):
        with patch("dmt.fetch_dependabot_prs", return_value=[make_pr()]):
            with patch("dmt.select_prs", return_value=None):
                result = dmt.main()
    assert result == 0
    assert "Aborted" in capsys.readouterr().out


def test_main_no_prs_selected_when_empty_list(capsys):
    with patch("sys.argv", ["dmt"]):
        with patch("dmt.fetch_dependabot_prs", return_value=[make_pr()]):
            with patch("dmt.select_prs", return_value=[]):
                result = dmt.main()
    assert result == 0
    assert "No PRs selected" in capsys.readouterr().out
