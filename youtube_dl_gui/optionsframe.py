"""yt-dlg module responsible for the options window. """
from __future__ import annotations

import os
from typing import TYPE_CHECKING, Callable, cast

import wx
import wx.adv

from .darktheme import dark_mode
from .flagart import catalog
from .formats import AUDIO_FORMATS, OUTPUT_FORMATS, VIDEO_FORMATS
from .info import __appname__
from .utils import IS_WINDOWS, YOUTUBEDL_BIN, YTDLP_BIN, get_key
from .widgets import LogGUI

if TYPE_CHECKING:
    from .mainframe import MainFrame

_: Callable[[str], str] = wx.GetTranslation
# REFACTOR Move all formats, etc to formats.py


class OptionsFrame(wx.Frame):
    """yt-dlg options frame class.

    Args:
        parent (MainFrame): Parent class.

    """

    FRAMES_MIN_SIZE: tuple[int, int] = (500, 520)

    def __init__(self, parent: MainFrame, darkmode: bool = False):
        wx.Frame.__init__(
            self,
            parent,
            title=_("Options"),
            size=parent.opt_manager.options["opts_win_size"],
        )
        self.parent = parent
        self.opt_manager = self.parent.opt_manager
        self.log_manager = self.parent.log_manager
        self.app_icon: wx.Icon | None = self.parent.app_icon

        if self.app_icon:
            self.SetIcon(self.app_icon)

        self.__dark_mode: bool = darkmode
        self._was_shown: bool = False

        # Create options frame basic components
        self.panel = wx.Panel(self)

        self.notebook = wx.Notebook(self.panel)
        self.separator_line = wx.StaticLine(self.panel)
        self.reset_button = wx.Button(self.panel, label=_("Reset"))
        self.close_button = wx.Button(self.panel, label=_("Close"))

        # Create tabs
        tab_args: tuple[OptionsFrame, wx.Notebook] = (self, self.notebook)

        self.tabs: tuple[
            tuple[GeneralTab, str],
            tuple[FormatsTab, str],
            tuple[DownloadsTab, str],
            tuple[AdvancedTab, str],
            tuple[ExtraTab, str],
        ] = (
            (GeneralTab(*tab_args), _("General")),
            (FormatsTab(*tab_args), _("Formats")),
            (DownloadsTab(*tab_args), _("Downloads")),
            (AdvancedTab(*tab_args), _("Advanced")),
            (ExtraTab(*tab_args), _("Extra")),
        )

        # Add tabs on notebook
        for tab, label in self.tabs:
            self.notebook.AddPage(tab, label)

        # Bind events
        self.Bind(wx.EVT_BUTTON, self._on_reset, self.reset_button)
        self.Bind(wx.EVT_BUTTON, self._on_close, self.close_button)
        self.Bind(wx.EVT_CLOSE, self._on_close)

        self.SetMinSize(self.FRAMES_MIN_SIZE)

        self._set_layout()
        # Set Dar Theme for Notebook
        dark_mode(self.notebook, self.__dark_mode)
        self.load_all_options()

    def _set_layout(self) -> None:
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        main_sizer.Add(self.notebook, 1, wx.EXPAND | wx.ALL, border=5)
        main_sizer.Add(self.separator_line, 0, wx.EXPAND)

        buttons_sizer = wx.BoxSizer(wx.HORIZONTAL)
        buttons_sizer.Add(self.reset_button)
        buttons_sizer.AddSpacer(5)
        buttons_sizer.Add(self.close_button)

        main_sizer.Add(buttons_sizer, flag=wx.ALIGN_RIGHT | wx.ALL, border=5)

        self.panel.SetSizer(main_sizer)

        self.panel.Layout()

    # noinspection PyProtectedMember,PyUnusedLocal
    def _on_close(self, event) -> None:
        """Event handler for wx.EVT_CLOSE event."""
        self.save_all_options()
        # REFACTOR Parent create specific callback
        self.parent._update_videoformat_combobox()
        self.Hide()

    # noinspection PyUnusedLocal
    def _on_reset(self, event) -> None:
        """Event handler for the reset button wx.EVT_BUTTON event."""
        self.reset()
        self.parent.reset()

    def reset(self) -> None:
        """Reset the default options."""
        self.opt_manager.load_default()
        self.load_all_options()

    def load_all_options(self) -> None:
        """Load all the options on each tab."""
        for tab, _label in self.tabs:
            cast("TabPanel", tab).load_options()

    def save_all_options(self) -> None:
        """Save all the options from all the tabs back to the OptionsManager."""
        for tab, _label in self.tabs:
            cast("TabPanel", tab).save_options()

    def Show(self, *args, **kwargs) -> None:
        """Shows options frame centered"""
        # CenterOnParent can't go to main frame's __init__ as main frame may change
        # own position and options frame won't be centered on main frame anymore.
        if not self._was_shown:
            self._was_shown = True
            self.CenterOnParent()
        return wx.Frame.Show(self, *args, **kwargs)

    def is_dark(self) -> bool:
        return self.__dark_mode


class TabPanel(wx.Panel):
    """Main tab class from which each tab inherits.

    Args:
        parent (OptionsFrame): The parent of all tabs.

        notebook (wx.Notebook): The container for each tab.

    Notes:
        In order to use a different size you must overwrite the below *_SIZE
        attributes on the corresponding child object.

    """

    CHECKBOX_SIZE: tuple[int, int] = wx.DefaultSize
    if IS_WINDOWS:
        # Make checkboxes look the same on Windows
        CHECKBOX_SIZE = (-1, 20)

    BUTTONS_SIZE: tuple[int, int] = wx.DefaultSize
    TEXTCTRL_SIZE: tuple[int, int] = wx.DefaultSize
    SPINCTRL_SIZE: tuple[int, int] = wx.DefaultSize

    CHECKLISTBOX_SIZE: tuple[int, int] = (-1, 80)
    LISTBOX_SIZE: tuple[int, int] = (-1, 80)

    def __init__(self, parent: OptionsFrame, notebook: wx.Notebook):
        super().__init__(notebook)
        # REFACTOR Maybe add methods to access those
        # save_options(key, value)
        # load_options(key)
        self.opt_manager = parent.opt_manager
        self.log_manager = parent.log_manager
        self.app_icon = parent.app_icon

        self.reset_handler = parent.reset

    def load_options(self):
        return NotImplemented

    def save_options(self):
        return NotImplemented

    # Shortcut methods below

    def crt_button(
        self, label: str, event_handler: Callable | None = None
    ) -> wx.Button:
        button = wx.Button(self, label=label, size=self.BUTTONS_SIZE)

        if event_handler:
            button.Bind(wx.EVT_BUTTON, event_handler)

        return button

    def crt_checkbox(
        self, label: str, event_handler: Callable | None = None
    ) -> wx.CheckBox:
        checkbox = wx.CheckBox(self, label=label, size=self.CHECKBOX_SIZE)

        if event_handler:
            checkbox.Bind(wx.EVT_CHECKBOX, event_handler)

        return checkbox

    def crt_textctrl(self, style: int | None = None) -> wx.TextCtrl:
        if style is not None:
            return wx.TextCtrl(self, size=self.TEXTCTRL_SIZE, style=style)

        return wx.TextCtrl(self, size=self.TEXTCTRL_SIZE)

    def crt_combobox(
        self, choices, size=(-1, -1), event_handler: Callable | None = None
    ) -> wx.ComboBox:
        combobox = wx.ComboBox(self, choices=choices, size=size, style=wx.CB_READONLY)

        if event_handler:
            combobox.Bind(wx.EVT_COMBOBOX, event_handler)

        return combobox

    def crt_bitmap_combobox(
        self,
        choices: list[tuple[str, str]],
        size: tuple[int, int] = (-1, -1),
        event_handler: Callable | None = None,
    ) -> wx.adv.BitmapComboBox:
        combobox = wx.adv.BitmapComboBox(self, size=size, style=wx.CB_READONLY)

        for item in choices:
            lang_code, lang_name = item
            _lang, country = lang_code.split("_")

            if country in catalog:
                flag_bmp: wx.Bitmap = catalog[country].GetBitmap()
            else:
                flag_bmp = catalog["BLANK"].GetBitmap()

            combobox.Append(lang_name, flag_bmp)

        if event_handler:
            combobox.Bind(wx.EVT_COMBOBOX, event_handler)

        return combobox

    def crt_spinctrl(
        self,
        spin_range: tuple[int, int] = (0, 9999),
        size: tuple[int, int] | None = None,
    ) -> wx.SpinCtrl:
        if not size:
            size = self.SPINCTRL_SIZE if IS_WINDOWS else (130, -1)
        spinctrl = wx.SpinCtrl(self, size=size)
        spinctrl.SetRange(*spin_range)

        return spinctrl

    def crt_statictext(self, label: str) -> wx.StaticText:
        return wx.StaticText(self, wx.ID_ANY, label)

    def crt_staticbox(self, label: str) -> wx.StaticBox:
        return wx.StaticBox(self, wx.ID_ANY, label)

    def crt_checklistbox(
        self, choices: list[str] | None, style: int | None = None
    ) -> wx.CheckListBox:
        if style is not None:
            return wx.CheckListBox(
                self, choices=choices, style=style, size=self.CHECKLISTBOX_SIZE
            )

        return wx.CheckListBox(self, choices=choices, size=self.CHECKLISTBOX_SIZE)

    def crt_listbox(
        self, choices: list[str] | None, style: int | None = None
    ) -> wx.ListBox:
        if style is not None:
            return wx.ListBox(
                self, choices=choices, style=style, size=self.LISTBOX_SIZE
            )

        return wx.ListBox(self, choices=choices, size=self.LISTBOX_SIZE)


class GeneralTab(TabPanel):
    OUTPUT_TEMPLATES: list[str] = [
        "Id",
        "Title",
        "Ext",
        "Uploader",
        "Resolution",
        "Autonumber",
        "",
        "View Count",
        "Like Count",
        "Dislike Count",
        "Comment Count",
        "Average Rating",
        "Age Limit",
        "Width",
        "Height",
        "Extractor",
        "",
        "Playlist",
        "Playlist Index",
    ]

    BUTTONS_SIZE: tuple[int, int] = (35, -1)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        _underscore: Callable = _

        for key, value in OUTPUT_FORMATS.items():
            OUTPUT_FORMATS[key] = _underscore(value)

        # Lang code = <ISO 639-1>_<ISO 3166-1 alpha-2>
        self.LOCALE_NAMES: dict[str, str] = {
            "sq_AL": _("Albanian"),
            "ar_SA": _("Arabic"),
            "es_CU": _("Cuba"),
            "cs_CZ": _("Czech"),
            "de_DE": _("German"),
            "en_US": _("English"),
            "fr_FR": _("French"),
            "it_IT": _("Italian"),
            "ja_JP": _("Japanese"),
            "ko_KR": _("Korean"),
            "pl_PL": _("Polish"),
            "pt_BR": _("Portuguese"),
            "ru_RU": _("Russian"),
            "sk_SK": _("Slovak"),
            "es_ES": _("Spanish"),
            "zh_CN": _("Simplified Chinese"),
            "zh_TW": _("Traditional Chinese"),
        }

        self.language_label = self.crt_statictext(_("Language"))
        self.language_combobox = self.crt_bitmap_combobox(
            list(self.LOCALE_NAMES.items()), event_handler=self._on_restart
        )

        self.filename_format_label = self.crt_statictext(_("Filename format"))
        self.filename_format_combobox = self.crt_combobox(
            list(OUTPUT_FORMATS.values()), event_handler=self._on_filename
        )
        self.filename_custom_format = self.crt_textctrl()
        self.filename_custom_format_button = self.crt_button("...", self._on_format)

        self.filename_opts_label = self.crt_statictext(_("Filename options"))
        self.filename_ascii_checkbox = self.crt_checkbox(
            _("Restrict filenames to ASCII")
        )

        self.more_opts_label = self.crt_statictext(_("More options"))
        self.dark_mode_checkbox = self.crt_checkbox(
            _("Dark theme"), event_handler=self._on_restart
        )
        self.confirm_exit_checkbox = self.crt_checkbox(_("Confirm on exit"))
        self.confirm_deletion_checkbox = self.crt_checkbox(_("Confirm item deletion"))
        self.show_completion_popup_checkbox = self.crt_checkbox(
            _("Inform me on download completion")
        )

        self.shutdown_checkbox = self.crt_checkbox(
            _("Shutdown on download completion"), event_handler=self._on_shutdown
        )
        self.sudo_textctrl = self.crt_textctrl(wx.TE_PASSWORD)

        # Build the menu for the custom format button
        self.custom_format_menu = self._build_custom_format_menu()

        self._set_layout()

        if IS_WINDOWS:
            self.sudo_textctrl.Hide()

        self.sudo_textctrl.SetToolTip(wx.ToolTip(_("SUDO password")))

    def _set_layout(self) -> None:
        main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        vertical_sizer = wx.BoxSizer(wx.VERTICAL)

        vertical_sizer.Add(self.language_label)
        vertical_sizer.Add(self.language_combobox, flag=wx.EXPAND | wx.ALL, border=5)

        vertical_sizer.Add(self.filename_format_label, flag=wx.TOP, border=5)
        vertical_sizer.Add(
            self.filename_format_combobox, flag=wx.EXPAND | wx.ALL, border=5
        )

        custom_format_sizer = wx.BoxSizer(wx.HORIZONTAL)
        custom_format_sizer.Add(
            self.filename_custom_format, 1, wx.ALIGN_CENTER_VERTICAL
        )
        custom_format_sizer.AddSpacer(5)
        custom_format_sizer.Add(self.filename_custom_format_button)

        vertical_sizer.Add(
            custom_format_sizer,
            flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM,
            border=5,
        )

        vertical_sizer.Add(self.filename_opts_label, flag=wx.TOP, border=5)
        vertical_sizer.Add(self.filename_ascii_checkbox, flag=wx.ALL, border=5)

        vertical_sizer.Add(self.more_opts_label, flag=wx.TOP, border=5)
        vertical_sizer.Add(self.dark_mode_checkbox, flag=wx.ALL, border=5)
        vertical_sizer.Add(
            self.confirm_exit_checkbox,
            flag=wx.LEFT | wx.RIGHT | wx.BOTTOM,
            border=5,
        )
        vertical_sizer.Add(
            self.confirm_deletion_checkbox,
            flag=wx.LEFT | wx.RIGHT | wx.BOTTOM,
            border=5,
        )
        vertical_sizer.Add(
            self.show_completion_popup_checkbox,
            flag=wx.LEFT | wx.RIGHT | wx.BOTTOM,
            border=5,
        )

        shutdown_sizer = wx.BoxSizer(wx.HORIZONTAL)
        shutdown_sizer.Add(self.shutdown_checkbox)
        shutdown_sizer.AddSpacer(-1)
        shutdown_sizer.Add(self.sudo_textctrl, 1)

        vertical_sizer.Add(
            shutdown_sizer, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=5
        )

        main_sizer.Add(vertical_sizer, 1, wx.EXPAND | wx.ALL, border=5)
        self.SetSizer(main_sizer)

    def _build_custom_format_menu(self) -> wx.Menu:
        menu = wx.Menu()

        for template in self.OUTPUT_TEMPLATES:
            if template:
                menu_item = menu.Append(wx.ID_ANY, template)
                menu.Bind(wx.EVT_MENU, self._on_template, menu_item)
            else:
                menu.AppendSeparator()

        return menu

    def _on_template(self, event) -> None:
        """Event handler for the wx.EVT_MENU of the custom_format_menu menu items."""
        label: str = self.custom_format_menu.GetLabelText(event.GetId())
        label = label.lower().replace(" ", "_")

        custom_format: str = self.filename_custom_format.GetValue()

        prefix: str = "." if label == "ext" else "-"
        if not custom_format or custom_format[-1] == os.sep:
            # If the custom format is empty or ends with path separator
            # remove the prefix
            prefix = ""

        template: str = f"{prefix}%({label})s"
        self.filename_custom_format.SetValue(custom_format + template)

    def _on_format(self, event) -> None:
        """Event handler for the wx.EVT_BUTTON of the filename_custom_format_button."""
        event_object_pos = event.EventObject.GetPosition()
        event_object_height = event.EventObject.GetSize()[1]
        event_object_pos = (
            event_object_pos[0],
            event_object_pos[1] + event_object_height,
        )
        self.PopupMenu(self.custom_format_menu, event_object_pos)

    # noinspection PyUnusedLocal
    def _on_restart(self, event) -> None:
        """Event handler for the wx.EVT_COMBOBOX of the language_combobox."""
        wx.MessageBox(
            _("In order for the changes to take effect please restart {0}").format(
                __appname__
            ),
            _("Restart"),
            wx.OK | wx.ICON_INFORMATION,
            self,
        )

    # noinspection PyUnusedLocal
    def _on_filename(self, event) -> None:
        """Event handler for the wx.EVT_COMBOBOX of the filename_format_combobox."""
        custom_selected: bool = (
            self.filename_format_combobox.GetValue() == OUTPUT_FORMATS["3"]
        )

        self.filename_custom_format.Enable(custom_selected)
        self.filename_custom_format_button.Enable(custom_selected)

    # noinspection PyUnusedLocal
    def _on_shutdown(self, event) -> None:
        """Event handler for the wx.EVT_CHECKBOX of the shutdown_checkbox."""
        self.sudo_textctrl.Enable(self.shutdown_checkbox.GetValue())

    def load_options(self) -> None:
        self.language_combobox.SetValue(
            self.LOCALE_NAMES.get(self.opt_manager.options["locale_name"], _("English"))
        )
        self.filename_format_combobox.SetValue(
            OUTPUT_FORMATS[self.opt_manager.options["output_format"]]
        )
        self.filename_custom_format.SetValue(
            self.opt_manager.options["output_template"]
        )
        self.filename_ascii_checkbox.SetValue(
            self.opt_manager.options["restrict_filenames"]
        )
        self.dark_mode_checkbox.SetValue(self.opt_manager.options["dark_mode"])
        self.shutdown_checkbox.SetValue(self.opt_manager.options["shutdown"])
        self.sudo_textctrl.SetValue(self.opt_manager.options["sudo_password"])
        self.confirm_exit_checkbox.SetValue(self.opt_manager.options["confirm_exit"])
        self.show_completion_popup_checkbox.SetValue(
            self.opt_manager.options["show_completion_popup"]
        )
        self.confirm_deletion_checkbox.SetValue(
            self.opt_manager.options["confirm_deletion"]
        )

        # REFACTOR Automatically call on the new methods
        # save_options
        # load_options
        # NOTE Maybe on init add callback?
        self._on_filename(None)
        self._on_shutdown(None)

    def save_options(self) -> None:
        self.opt_manager.options["locale_name"] = get_key(
            self.language_combobox.GetValue(), self.LOCALE_NAMES, "en_US"
        )
        self.opt_manager.options["output_format"] = get_key(
            self.filename_format_combobox.GetValue(), OUTPUT_FORMATS, "1"
        )
        self.opt_manager.options[
            "output_template"
        ] = self.filename_custom_format.GetValue()
        self.opt_manager.options[
            "restrict_filenames"
        ] = self.filename_ascii_checkbox.GetValue()
        self.opt_manager.options["dark_mode"] = self.dark_mode_checkbox.GetValue()
        self.opt_manager.options["shutdown"] = self.shutdown_checkbox.GetValue()
        self.opt_manager.options["sudo_password"] = self.sudo_textctrl.GetValue()
        self.opt_manager.options["confirm_exit"] = self.confirm_exit_checkbox.GetValue()
        self.opt_manager.options[
            "show_completion_popup"
        ] = self.show_completion_popup_checkbox.GetValue()
        self.opt_manager.options[
            "confirm_deletion"
        ] = self.confirm_deletion_checkbox.GetValue()


class FormatsTab(TabPanel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.AUDIO_QUALITY: dict[str, str] = {
            "0": _("high"),
            "5": _("mid"),
            "9": _("low"),
        }

        self.video_formats_label = self.crt_statictext(_("Video formats"))
        self.video_formats_checklistbox = self.crt_checklistbox(
            list(VIDEO_FORMATS.values())
        )

        self.audio_formats_label = self.crt_statictext(_("Audio formats"))
        self.audio_formats_checklistbox = self.crt_checklistbox(
            list(AUDIO_FORMATS.values())
        )

        self.post_proc_opts_label = self.crt_statictext(_("Post-Process options"))
        self.keep_video_checkbox = self.crt_checkbox(_("Keep original files"))
        self.extract_audio_checkbox = self.crt_checkbox(
            _("Extract audio from video file")
        )
        self.embed_thumbnail_checkbox = self.crt_checkbox(
            _("Embed thumbnail in audio file")
        )
        self.add_metadata_checkbox = self.crt_checkbox(_("Add metadata to file"))

        self.audio_quality_label = self.crt_statictext(_("Audio quality"))
        self.audio_quality_combobox = self.crt_combobox(
            list(self.AUDIO_QUALITY.values())
        )

        self._set_layout()

    def _set_layout(self) -> None:
        main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        vertical_sizer = wx.BoxSizer(wx.VERTICAL)

        vertical_sizer.Add(self.video_formats_label)
        vertical_sizer.Add(
            self.video_formats_checklistbox, 1, wx.EXPAND | wx.ALL, border=5
        )

        vertical_sizer.Add(self.audio_formats_label, flag=wx.TOP, border=5)
        vertical_sizer.Add(
            self.audio_formats_checklistbox, 1, wx.EXPAND | wx.ALL, border=5
        )

        vertical_sizer.Add(self.post_proc_opts_label, flag=wx.TOP, border=5)
        vertical_sizer.Add(self.keep_video_checkbox, flag=wx.ALL, border=5)
        vertical_sizer.Add(
            self.extract_audio_checkbox, flag=wx.LEFT | wx.RIGHT | wx.BOTTOM, border=5
        )
        vertical_sizer.Add(
            self.embed_thumbnail_checkbox, flag=wx.LEFT | wx.RIGHT | wx.BOTTOM, border=5
        )
        vertical_sizer.Add(
            self.add_metadata_checkbox, flag=wx.LEFT | wx.RIGHT | wx.BOTTOM, border=5
        )

        audio_quality_sizer = wx.BoxSizer(wx.HORIZONTAL)
        audio_quality_sizer.Add(self.audio_quality_label, flag=wx.ALIGN_CENTER_VERTICAL)
        audio_quality_sizer.AddSpacer(20)
        audio_quality_sizer.Add(self.audio_quality_combobox)

        vertical_sizer.Add(
            audio_quality_sizer, flag=wx.LEFT | wx.RIGHT | wx.BOTTOM, border=5
        )

        main_sizer.Add(vertical_sizer, 1, wx.EXPAND | wx.ALL, border=5)
        self.SetSizer(main_sizer)

    def load_options(self) -> None:
        checked_video_formats: list[str] = [
            VIDEO_FORMATS[get_key(vformat, VIDEO_FORMATS)]
            for vformat in self.opt_manager.options["selected_video_formats"]
        ]
        self.video_formats_checklistbox.SetCheckedStrings(checked_video_formats)
        checked_audio_formats: list[str] = [
            AUDIO_FORMATS[get_key(aformat, AUDIO_FORMATS)]
            for aformat in self.opt_manager.options["selected_audio_formats"]
        ]
        self.audio_formats_checklistbox.SetCheckedStrings(checked_audio_formats)
        self.keep_video_checkbox.SetValue(self.opt_manager.options["keep_video"])
        self.audio_quality_combobox.SetValue(
            self.AUDIO_QUALITY[self.opt_manager.options["audio_quality"]]
        )
        self.extract_audio_checkbox.SetValue(self.opt_manager.options["to_audio"])
        self.embed_thumbnail_checkbox.SetValue(
            self.opt_manager.options["embed_thumbnail"]
        )
        self.add_metadata_checkbox.SetValue(self.opt_manager.options["add_metadata"])

    def save_options(self):
        checked_video_formats: list[str] = [
            VIDEO_FORMATS[get_key(vformat, VIDEO_FORMATS)]
            for vformat in self.video_formats_checklistbox.GetCheckedStrings()
        ]
        self.opt_manager.options["selected_video_formats"] = checked_video_formats
        checked_audio_formats: list[str] = [
            AUDIO_FORMATS[get_key(aformat, AUDIO_FORMATS)]
            for aformat in self.audio_formats_checklistbox.GetCheckedStrings()
        ]
        self.opt_manager.options["selected_audio_formats"] = checked_audio_formats
        self.opt_manager.options["keep_video"] = self.keep_video_checkbox.GetValue()
        self.opt_manager.options["audio_quality"] = get_key(
            self.audio_quality_combobox.GetValue(), self.AUDIO_QUALITY, "5"
        )
        self.opt_manager.options["to_audio"] = self.extract_audio_checkbox.GetValue()
        self.opt_manager.options[
            "embed_thumbnail"
        ] = self.embed_thumbnail_checkbox.GetValue()
        self.opt_manager.options["add_metadata"] = self.add_metadata_checkbox.GetValue()


class DownloadsTab(TabPanel):
    FILESIZES: dict[str, str] = {
        "": "Bytes",
        "k": "Kilobytes",
        "m": "Megabytes",
        "g": "Gigabytes",
        "t": "Terabytes",
        "p": "Petabytes",
        "e": "Exabytes",
        "z": "Zettabytes",
        "y": "Yottabytes",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Lang code = ISO 639-1
        self.SUBS_LANG: dict[str, str] = {
            "en": _("English"),
            "fr": _("French"),
            "de": _("German"),
            "el": _("Greek"),
            "he": _("Hebrew"),
            "it": _("Italian"),
            "pl": _("Polish"),
            "pt": _("Portuguese"),
            "ru": _("Russian"),
            "es": _("Spanish"),
            "sv": _("Swedish"),
            "tr": _("Turkish"),
            "sq": _("Albanian"),
            "zh": _("Chinese"),
        }

        self.SUBS_CHOICES: list[str] = [
            _("None"),
            _("Automatic subtitles (YOUTUBE ONLY)"),
            _("All available subtitles"),
            _("Subtitles by language"),
        ]

        self.subtitles_label = self.crt_statictext(_("Subtitles"))
        self.subtitles_combobox = self.crt_combobox(
            self.SUBS_CHOICES, event_handler=self._on_subtitles
        )
        self.subtitles_lang_listbox = self.crt_listbox(list(self.SUBS_LANG.values()))

        self.subtitles_opts_label = self.crt_statictext(_("Subtitles options"))
        self.embed_subs_checkbox = self.crt_checkbox(
            _("Embed subtitles into video file (mp4 ONLY)")
        )
        self.write_desc_checkbox = self.crt_checkbox(_("Write description to file"))
        self.write_info_checkbox = self.crt_checkbox(_("Write info to (.json) file"))
        self.write_thumbnail_checkbox = self.crt_checkbox(_("Write thumbnail to disk"))
        self.no_overwrites_checkbox = self.crt_checkbox(_("Do not overwrite any file"))
        self.no_check_certificates_checkbox = self.crt_checkbox(_("Suppress HTTPS certificate validation"))

        self.playlist_box = self.crt_staticbox(_("Playlist"))

        self.playlist_start_label = self.crt_statictext(_("Start"))
        self.playlist_start_spinctrl = self.crt_spinctrl((1, 9999))
        self.playlist_stop_label = self.crt_statictext(_("Stop"))
        self.playlist_stop_spinctrl = self.crt_spinctrl()
        self.playlist_max_label = self.crt_statictext(_("Max"))
        self.playlist_max_spinctrl = self.crt_spinctrl()

        self.filesize_box = self.crt_staticbox(_("Filesize"))

        self.filesize_max_label = self.crt_statictext(_("Max"))
        self.filesize_max_spinctrl = self.crt_spinctrl((0, 1024))
        self.filesize_max_sizeunit_combobox = self.crt_combobox(
            list(self.FILESIZES.values())
        )
        self.filesize_min_label = self.crt_statictext(_("Min"))
        self.filesize_min_spinctrl = self.crt_spinctrl((0, 1024))
        self.filesize_min_sizeunit_combobox = self.crt_combobox(
            list(self.FILESIZES.values())
        )

        self._set_layout()

    def _set_layout(self) -> None:
        main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        vertical_sizer = wx.BoxSizer(wx.VERTICAL)

        vertical_sizer.Add(self.subtitles_label)
        vertical_sizer.Add(self.subtitles_combobox, flag=wx.EXPAND | wx.ALL, border=5)
        vertical_sizer.Add(
            self.subtitles_lang_listbox,
            1,
            wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM,
            border=5,
        )

        vertical_sizer.Add(self.subtitles_opts_label, flag=wx.TOP, border=5)
        vertical_sizer.Add(self.embed_subs_checkbox, flag=wx.ALL, border=5)

        plist_and_fsize_sizer = wx.BoxSizer(wx.HORIZONTAL)
        plist_and_fsize_sizer.Add(self._build_playlist_sizer(), 1, wx.EXPAND)
        plist_and_fsize_sizer.AddSpacer(5)
        plist_and_fsize_sizer.Add(self._build_filesize_sizer(), 1, wx.EXPAND)

        vertical_sizer.Add(plist_and_fsize_sizer, 1, wx.EXPAND | wx.TOP, border=5)

        lower_sizer = wx.GridBagSizer(5, -1)
        lower_sizer.Add(self.write_desc_checkbox, (0, 0), flag=wx.RIGHT, border=15)
        lower_sizer.Add(self.write_info_checkbox, (1, 0))
        lower_sizer.Add(self.write_thumbnail_checkbox, (2, 0))
        lower_sizer.Add(self.no_overwrites_checkbox, (0, 1))
        lower_sizer.Add(self.no_check_certificates_checkbox, (1, 1))
        vertical_sizer.Add(lower_sizer, 1, wx.EXPAND | wx.TOP, border=5)

        main_sizer.Add(vertical_sizer, 1, wx.EXPAND | wx.ALL, border=5)
        self.SetSizer(main_sizer)

    def _build_playlist_sizer(self) -> wx.StaticBoxSizer:
        playlist_box_sizer = wx.StaticBoxSizer(self.playlist_box, wx.VERTICAL)
        playlist_box_sizer.AddSpacer(10)

        border = wx.GridBagSizer(5, 40)

        border.Add(self.playlist_start_label, (0, 0), flag=wx.ALIGN_CENTER_VERTICAL)
        border.Add(self.playlist_start_spinctrl, (0, 1))

        border.Add(self.playlist_stop_label, (1, 0), flag=wx.ALIGN_CENTER_VERTICAL)
        border.Add(self.playlist_stop_spinctrl, (1, 1))

        border.Add(self.playlist_max_label, (2, 0), flag=wx.ALIGN_CENTER_VERTICAL)
        border.Add(self.playlist_max_spinctrl, (2, 1))

        playlist_box_sizer.Add(border, flag=wx.ALIGN_CENTER)

        return playlist_box_sizer

    def _build_filesize_sizer(self) -> wx.StaticBoxSizer:
        filesize_box_sizer = wx.StaticBoxSizer(self.filesize_box, wx.VERTICAL)

        border = wx.GridBagSizer(5, 20)

        border.Add(self.filesize_max_label, (0, 0), (1, 2), wx.ALIGN_CENTER_HORIZONTAL)

        border.Add(self.filesize_max_spinctrl, (1, 0))
        border.Add(self.filesize_max_sizeunit_combobox, (1, 1))

        border.Add(self.filesize_min_label, (2, 0), (1, 2), wx.ALIGN_CENTER_HORIZONTAL)

        border.Add(self.filesize_min_spinctrl, (3, 0))
        border.Add(self.filesize_min_sizeunit_combobox, (3, 1))

        filesize_box_sizer.Add(border, flag=wx.ALIGN_CENTER)

        return filesize_box_sizer

    # noinspection PyUnusedLocal
    def _on_subtitles(self, event) -> None:
        """Event handler for the wx.EVT_COMBOBOX of the subtitles_combobox."""
        self.subtitles_lang_listbox.Enable(
            self.subtitles_combobox.GetValue() == self.SUBS_CHOICES[-1]
        )

    def load_options(self) -> None:
        # NOTE Find a better way to do this
        if self.opt_manager.options["write_subs"]:
            self.subtitles_combobox.SetValue(self.SUBS_CHOICES[3])
        elif self.opt_manager.options["write_all_subs"]:
            self.subtitles_combobox.SetValue(self.SUBS_CHOICES[2])
        elif self.opt_manager.options["write_auto_subs"]:
            self.subtitles_combobox.SetValue(self.SUBS_CHOICES[1])
        else:
            self.subtitles_combobox.SetValue(self.SUBS_CHOICES[0])

        self.subtitles_lang_listbox.SetStringSelection(
            self.SUBS_LANG[self.opt_manager.options["subs_lang"]]
        )
        self.embed_subs_checkbox.SetValue(self.opt_manager.options["embed_subs"])
        self.write_desc_checkbox.SetValue(self.opt_manager.options['write_description'])
        self.write_info_checkbox.SetValue(self.opt_manager.options['write_info'])
        self.write_thumbnail_checkbox.SetValue(self.opt_manager.options['write_thumbnail'])
        self.no_overwrites_checkbox.SetValue(self.opt_manager.options['no_overwrites'])
        self.no_check_certificates_checkbox.SetValue(self.opt_manager.options['no_check_certificates'])
        self.playlist_start_spinctrl.SetValue(
            self.opt_manager.options["playlist_start"]
        )
        self.playlist_stop_spinctrl.SetValue(self.opt_manager.options["playlist_end"])
        self.playlist_max_spinctrl.SetValue(self.opt_manager.options["max_downloads"])
        self.filesize_min_spinctrl.SetValue(self.opt_manager.options["min_filesize"])
        self.filesize_max_spinctrl.SetValue(self.opt_manager.options["max_filesize"])
        self.filesize_min_sizeunit_combobox.SetValue(
            self.FILESIZES[self.opt_manager.options["min_filesize_unit"]]
        )
        self.filesize_max_sizeunit_combobox.SetValue(
            self.FILESIZES[self.opt_manager.options["max_filesize_unit"]]
        )

        self._on_subtitles(None)

    def save_options(self) -> None:
        subs_choice: int = self.SUBS_CHOICES.index(self.subtitles_combobox.GetValue())

        self.opt_manager.options["write_subs"] = False
        self.opt_manager.options["write_all_subs"] = False
        self.opt_manager.options["write_auto_subs"] = False

        if subs_choice == 1:
            self.opt_manager.options["write_auto_subs"] = True
        elif subs_choice == 2:
            self.opt_manager.options["write_all_subs"] = True
        elif subs_choice == 3:
            self.opt_manager.options["write_subs"] = True

        self.opt_manager.options["subs_lang"] = get_key(
            self.subtitles_lang_listbox.GetStringSelection(), self.SUBS_LANG, "en"
        )
        self.opt_manager.options["embed_subs"] = self.embed_subs_checkbox.GetValue()
        self.opt_manager.options['write_description'] = self.write_desc_checkbox.GetValue()
        self.opt_manager.options['write_info'] = self.write_info_checkbox.GetValue()
        self.opt_manager.options['write_thumbnail'] = self.write_thumbnail_checkbox.GetValue()
        self.opt_manager.options['no_overwrites'] = self.no_overwrites_checkbox.GetValue()
        self.opt_manager.options['no_check_certificates'] = self.no_check_certificates_checkbox.GetValue()
        self.opt_manager.options[
            "playlist_start"
        ] = self.playlist_start_spinctrl.GetValue()
        self.opt_manager.options[
            "playlist_end"
        ] = self.playlist_stop_spinctrl.GetValue()
        self.opt_manager.options[
            "max_downloads"
        ] = self.playlist_max_spinctrl.GetValue()
        self.opt_manager.options["min_filesize"] = self.filesize_min_spinctrl.GetValue()
        self.opt_manager.options["max_filesize"] = self.filesize_max_spinctrl.GetValue()
        self.opt_manager.options["min_filesize_unit"] = get_key(
            self.filesize_min_sizeunit_combobox.GetValue(), self.FILESIZES, ""
        )
        self.opt_manager.options["max_filesize_unit"] = get_key(
            self.filesize_max_sizeunit_combobox.GetValue(), self.FILESIZES, ""
        )


class AdvancedTab(TabPanel):
    TEXTCTRL_SIZE: tuple[int, int] = (300, -1)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parent: OptionsFrame = args[0]
        self.workers_number_label = self.crt_statictext(_("Workers number"))
        self.workers_number_spinctrl = self.crt_spinctrl((1, 99))
        self.retries_label = self.crt_statictext(_("Retries"))
        self.retries_spinctrl = self.crt_spinctrl((1, 999))

        self.auth_label = self.crt_statictext(_("Authentication"))

        self.username_label = self.crt_statictext(_("Username"))
        self.username_textctrl = self.crt_textctrl()
        self.password_label = self.crt_statictext(_("Password"))
        self.password_textctrl = self.crt_textctrl(wx.TE_PASSWORD)
        self.video_pass_label = self.crt_statictext(_("Video password"))
        self.video_pass_textctrl = self.crt_textctrl(wx.TE_PASSWORD)

        self.network_label = self.crt_statictext(_("Network"))

        self.proxy_label = self.crt_statictext(_("Proxy"))
        self.proxy_textctrl = self.crt_textctrl()
        self.useragent_label = self.crt_statictext(_("User agent"))
        self.useragent_textctrl = self.crt_textctrl()
        self.referer_label = self.crt_statictext(_("Referer"))
        self.referer_textctrl = self.crt_textctrl()

        self.ffmpeg_label = self.crt_statictext(_("FFmpeg"))

        self.ffmpeg_location_label = self.crt_statictext(_("FFmpeg location"))
        self.ffmpeg_location_textctrl = self.crt_textctrl()

        self.logging_label = self.crt_statictext(_("Logging"))

        self.enable_log_checkbox = self.crt_checkbox(
            _("Enable log"), self._on_enable_log
        )
        self.view_log_button = self.crt_button(_("View"), self._on_view)
        self.clear_log_button = self.crt_button(_("Clear"), self._on_clear)

        self._set_layout()

        if self.log_manager is None:
            self.view_log_button.Disable()
            self.clear_log_button.Disable()

    def _set_layout(self):
        main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        vertical_sizer = wx.BoxSizer(wx.VERTICAL)

        upper_sizer = wx.GridBagSizer(5, -1)

        # Set up workers_number box
        workers_number_sizer = wx.BoxSizer(wx.HORIZONTAL)
        workers_number_sizer.Add(self.workers_number_label, flag=wx.ALIGN_CENTER_VERTICAL)
        workers_number_sizer.AddSpacer(10)
        workers_number_sizer.Add(self.workers_number_spinctrl)

        # Set up retries box
        retries_sizer = wx.BoxSizer(wx.HORIZONTAL)
        retries_sizer.Add(self.retries_label, flag=wx.ALIGN_CENTER_VERTICAL)
        retries_sizer.AddSpacer(10)
        retries_sizer.Add(self.retries_spinctrl)

        upper_sizer.Add(workers_number_sizer, (0, 0))
        upper_sizer.Add(retries_sizer, (0, 2))
        upper_sizer.AddGrowableCol(1)
        vertical_sizer.Add(upper_sizer, flag=wx.EXPAND | wx.ALL, border=5)

        # Set up authentication box
        vertical_sizer.Add(self.auth_label, flag=wx.TOP, border=10)
        auth_sizer = wx.GridBagSizer(5, -1)

        auth_sizer.Add(self.username_label, (0, 0), flag=wx.ALIGN_CENTER_VERTICAL)
        auth_sizer.Add(self.username_textctrl, (0, 2))

        auth_sizer.Add(self.password_label, (1, 0), flag=wx.ALIGN_CENTER_VERTICAL)
        auth_sizer.Add(self.password_textctrl, (1, 2))

        auth_sizer.Add(self.video_pass_label, (2, 0), flag=wx.ALIGN_CENTER_VERTICAL)
        auth_sizer.Add(self.video_pass_textctrl, (2, 2))

        auth_sizer.AddGrowableCol(1)
        vertical_sizer.Add(auth_sizer, flag=wx.EXPAND | wx.ALL, border=5)

        # Set up network box
        vertical_sizer.Add(self.network_label, flag=wx.TOP, border=10)
        network_sizer = wx.GridBagSizer(5, -1)

        network_sizer.Add(self.proxy_label, (0, 0), flag=wx.ALIGN_CENTER_VERTICAL)
        network_sizer.Add(self.proxy_textctrl, (0, 2))

        network_sizer.Add(self.useragent_label, (1, 0), flag=wx.ALIGN_CENTER_VERTICAL)
        network_sizer.Add(self.useragent_textctrl, (1, 2))

        network_sizer.Add(self.referer_label, (2, 0), flag=wx.ALIGN_CENTER_VERTICAL)
        network_sizer.Add(self.referer_textctrl, (2, 2))

        network_sizer.AddGrowableCol(1)
        vertical_sizer.Add(network_sizer, flag=wx.EXPAND | wx.ALL, border=5)

        # Set up ffmpeg box
        vertical_sizer.Add(self.ffmpeg_label, flag=wx.TOP, border=10)
        ffmpeg_sizer = wx.GridBagSizer(5, -1)

        ffmpeg_sizer.Add(self.ffmpeg_location_label, (0, 0), flag=wx.ALIGN_CENTER_VERTICAL)
        ffmpeg_sizer.Add(self.ffmpeg_location_textctrl, (0, 2))

        ffmpeg_sizer.AddGrowableCol(1)
        vertical_sizer.Add(ffmpeg_sizer, flag=wx.EXPAND | wx.ALL, border=5)

        # Set up logging box
        vertical_sizer.Add(self.logging_label, flag=wx.TOP, border=10)

        logging_sizer = wx.BoxSizer(wx.HORIZONTAL)
        logging_sizer.Add(self.enable_log_checkbox)
        logging_sizer.AddSpacer(-1)
        logging_sizer.Add(self.view_log_button)
        logging_sizer.AddSpacer(5)
        logging_sizer.Add(self.clear_log_button)

        vertical_sizer.Add(logging_sizer, flag=wx.EXPAND | wx.ALL, border=5)

        main_sizer.Add(vertical_sizer, 1, wx.EXPAND | wx.ALL, border=5)
        self.SetSizer(main_sizer)

    # noinspection PyUnusedLocal
    def _on_enable_log(self, event) -> None:
        """Event handler for the wx.EVT_CHECKBOX of the enable_log_checkbox."""
        wx.MessageBox(
            _("In order for the changes to take effect please restart {0}").format(
                __appname__
            ),
            _("Restart"),
            wx.OK | wx.ICON_INFORMATION,
            self,
        )

    # noinspection PyUnusedLocal
    def _on_view(self, event) -> None:
        """Event handler for the wx.EVT_BUTTON of the view_log_button."""
        log_window = LogGUI(self.parent)
        log_window.load(self.log_manager.log_file)
        log_window.Show()

    # noinspection PyUnusedLocal
    def _on_clear(self, event) -> None:
        """Event handler for the wx.EVT_BUTTON of the clear_log_button."""
        if self.log_manager is not None:
            self.log_manager.clear()

    def load_options(self) -> None:
        self.workers_number_spinctrl.SetValue(self.opt_manager.options["workers_number"])
        self.retries_spinctrl.SetValue(self.opt_manager.options["retries"])
        self.username_textctrl.SetValue(self.opt_manager.options["username"])
        self.password_textctrl.SetValue(self.opt_manager.options["password"])
        self.video_pass_textctrl.SetValue(self.opt_manager.options["video_password"])
        self.proxy_textctrl.SetValue(self.opt_manager.options["proxy"])
        self.useragent_textctrl.SetValue(self.opt_manager.options["user_agent"])
        self.referer_textctrl.SetValue(self.opt_manager.options["referer"])
        self.ffmpeg_location_textctrl.SetValue(self.opt_manager.options["ffmpeg_location"])
        self.enable_log_checkbox.SetValue(self.opt_manager.options["enable_log"])

    def save_options(self) -> None:
        self.opt_manager.options["workers_number"] = self.workers_number_spinctrl.GetValue()
        self.opt_manager.options["retries"] = self.retries_spinctrl.GetValue()
        self.opt_manager.options["username"] = self.username_textctrl.GetValue()
        self.opt_manager.options["password"] = self.password_textctrl.GetValue()
        self.opt_manager.options["video_password"] = self.video_pass_textctrl.GetValue()
        self.opt_manager.options["proxy"] = self.proxy_textctrl.GetValue()
        self.opt_manager.options["user_agent"] = self.useragent_textctrl.GetValue()
        self.opt_manager.options["referer"] = self.referer_textctrl.GetValue()
        self.opt_manager.options["ffmpeg_location"] = self.ffmpeg_location_textctrl.GetValue()
        self.opt_manager.options["enable_log"] = self.enable_log_checkbox.GetValue()


class ExtraTab(TabPanel):
    CLI_BACKEND: list[str] = [YOUTUBEDL_BIN, YTDLP_BIN]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.cli_label = self.crt_statictext(_("CLI Backend"))
        self.cli_combobox = self.crt_combobox(self.CLI_BACKEND)

        self.cmdline_args_label = self.crt_statictext(
            _("CLI Backend command line options (e.g. --help)")
        )
        self.cmdline_args_textctrl = self.crt_textctrl(wx.TE_MULTILINE)

        self.extra_opts_label = self.crt_statictext(_("Extra options"))

        self.youtube_dl_debug_checkbox = self.crt_checkbox(_("Debug CLI Backend"))
        self.ignore_errors_checkbox = self.crt_checkbox(_("Ignore errors"))
        self.ignore_config_checkbox = self.crt_checkbox(_("Ignore CLI Backend config"))
        self.no_mtime_checkbox = self.crt_checkbox(_("No mtime"))
        self.native_hls_checkbox = self.crt_checkbox(_("Prefer native HLS"))

        self._set_layout()

    def _set_layout(self) -> None:
        main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        vertical_sizer = wx.BoxSizer(wx.VERTICAL)

        vertical_sizer.Add(self.cli_label)
        vertical_sizer.Add(self.cli_combobox, flag=wx.EXPAND | wx.ALL, border=5)
        vertical_sizer.Add(self.cmdline_args_label, flag=wx.TOP, border=5)
        vertical_sizer.Add(self.cmdline_args_textctrl, 1, wx.EXPAND | wx.ALL, border=5)
        vertical_sizer.Add(self.extra_opts_label, flag=wx.TOP, border=5)

        extra_opts_sizer = wx.WrapSizer()
        extra_opts_sizer.Add(self.youtube_dl_debug_checkbox)
        extra_opts_sizer.AddSpacer(5)
        extra_opts_sizer.Add(self.ignore_errors_checkbox)
        extra_opts_sizer.AddSpacer(5)
        extra_opts_sizer.Add(self.ignore_config_checkbox)
        extra_opts_sizer.AddSpacer(5)
        extra_opts_sizer.Add(self.no_mtime_checkbox)
        extra_opts_sizer.AddSpacer(5)
        extra_opts_sizer.Add(self.native_hls_checkbox)

        vertical_sizer.Add(extra_opts_sizer, flag=wx.ALL, border=5)

        main_sizer.Add(vertical_sizer, 1, wx.EXPAND | wx.ALL, border=5)
        self.SetSizer(main_sizer)

    @staticmethod
    def clean_cmd_args(args: str) -> str:
        return args.replace("'", "").replace('"', "")

    def load_options(self) -> None:
        self.cli_combobox.SetValue(
            self.opt_manager.options.get("cli_backend", YOUTUBEDL_BIN)
        )
        self.cmdline_args_textctrl.SetValue(self.opt_manager.options["cmd_args"])
        self.ignore_errors_checkbox.SetValue(self.opt_manager.options["ignore_errors"])
        self.youtube_dl_debug_checkbox.SetValue(
            self.opt_manager.options["youtube_dl_debug"]
        )
        self.ignore_config_checkbox.SetValue(self.opt_manager.options["ignore_config"])
        self.native_hls_checkbox.SetValue(self.opt_manager.options["native_hls"])
        self.no_mtime_checkbox.SetValue(self.opt_manager.options["nomtime"])

    def save_options(self) -> None:
        self.opt_manager.options["cli_backend"] = self.cli_combobox.GetValue()
        self.opt_manager.options["cmd_args"] = self.cmdline_args_textctrl.GetValue()
        self.opt_manager.options[
            "ignore_errors"
        ] = self.ignore_errors_checkbox.GetValue()
        self.opt_manager.options[
            "youtube_dl_debug"
        ] = self.youtube_dl_debug_checkbox.GetValue()
        self.opt_manager.options[
            "ignore_config"
        ] = self.ignore_config_checkbox.GetValue()
        self.opt_manager.options["native_hls"] = self.native_hls_checkbox.GetValue()
        self.opt_manager.options["nomtime"] = self.no_mtime_checkbox.GetValue()
