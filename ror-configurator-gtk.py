#!/usr/bin/python
# This source file is part of Rigs of Rods
# Copyright 2015 Artem Vorotnikov

# For more information, see http://www.rigsofrods.com/

# Rigs of Rods is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3, as
# published by the Free Software Foundation.

# Rigs of Rods is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Rigs of Rods.  If not, see <http://www.gnu.org/licenses/>.

"""This is a PyGObject-based GUI for Rigs of Rods configurator."""

import argparse
import ast
import os

from gi.repository import GdkPixbuf, Gtk, Gio, GLib

try:
    import pygeoip
    GEOIP_DATA = '/usr/share/GeoIP/GeoIP.dat'
    try:
        open(GEOIP_DATA)
        print("GeoIP data file", GEOIP_DATA, "opened successfully")
        GEOIP_ENABLED = True
    except:
        print("GeoIP data file not found. Disabling geolocation.")
        GEOIP_ENABLED = False
except ImportError:
    print("PyGeoIP not found. Disabling geolocation.")
    GEOIP_ENABLED = False

import server_stat

APP_CONFIG = os.path.join(os.path.dirname(__file__), "ror-configurator.ini")
UI_PATH = os.path.join(os.path.dirname(__file__), "ror-configurator-gtk.ui")

class Callbacks:
    """Responses to events from GUI"""
    def __init__(self, backend, user_settings_file, builder):
        self.backend = backend
        self.user_settings_file = user_settings_file
        self.builder = builder
    def cb_view_distance_limit_enabled_checkbutton_toggled(self, *args):
        """Toggles the status of view distance scale"""
        checkbutton = Gtk.Builder.get_object(self.builder, "ViewDistanceLimitEnabled_CheckButton")
        scale = Gtk.Builder.get_object(self.builder, "ViewDistanceLimit_Scale")

        if Gtk.ToggleButton.get_active(checkbutton) == True:
            Gtk.Widget.set_sensitive(scale, True)
        else:
            Gtk.Widget.set_sensitive(scale, False)

    def cb_fps_limit_enabled_checkbutton_toggled(self, *args):
        """Toggles the status of FPS limit scale"""
        checkbutton = Gtk.Builder.get_object(self.builder, "FpsLimitEnabled_CheckButton")
        scale = Gtk.Builder.get_object(self.builder, "FpsLimit_Scale")

        if Gtk.ToggleButton.get_active(checkbutton) == True:
            Gtk.Widget.set_sensitive(scale, True)
        else:
            Gtk.Widget.set_sensitive(scale, False)

    def cb_set_widget_sensitivity(self):
        """Sets sensitivity for dependent widgets."""
        self.cb_view_distance_limit_enabled_checkbutton_toggled(self)
        self.cb_fps_limit_enabled_checkbutton_toggled(self)

    def cb_btn_restore_clicked(self, *args):
        """Restores default configuration. Currently a stub."""
        print("Stub")

    def cb_btn_play_clicked(self, *args):
        """Stores the configuration and starts the game."""
        Settings.save(Settings)
        Gtk.main_quit()
        start_game(ror_path)

    def cb_btn_save_and_exit_clicked(self, *args):
        """Stores the configuration and exits."""
        settings = Settings(self.backend, self.user_settings_file, self.builder)
        settings.save()
        Gtk.main_quit()

    @staticmethod
    def cb_btn_about_clicked(self, window):
        """Opens the About dialog."""
        Gtk.Dialog.run(window)
        Gtk.Dialog.hide(window)

    @staticmethod
    def cb_quit(*args):
        """Exits the program."""
        Gtk.main_quit()

    @classmethod
    def cb_server_update_button_clicked(cls, listmodel, *data):
        """Refills the server list model"""
        ping_button = Gtk.Builder.get_object(App.builder, "PingingEnable_CheckButton")
        ping_column = Gtk.Builder.get_object(App.builder, "Ping_ServerList_TreeViewColumn")

        listmodel.clear()

        listing = server_stat.stat_master(server_stat.MASTER_URL, ping_button.get_active())
        Gtk.TreeViewColumn.set_visible(ping_column, ping_button.get_active())
        # Goodies for GUI
        for i in range(len(listing)):
            # Lock icon
            if listing[i][server_stat.MASTER_PASS_COLUMN[-1] - 1] == True:
                listing[i].append("network-wireless-encrypted-symbolic")
            else:
                listing[i].append(None)

            # Country flags
            if GEOIP_ENABLED == True:
                host = listing[i][server_stat.MASTER_HOST_COLUMN[-1] - 1].split(':')[0]
                try:
                    country_code = pygeoip.GeoIP(GEOIP_DATA).country_code_by_addr(host)
                except OSError:
                    country_code = pygeoip.GeoIP(GEOIP_DATA).country_code_by_name(host)
                except:
                    country_code = 'unknown'
            else:
                country_code = 'unknown'
            listing[i].append(GdkPixbuf.Pixbuf.new_from_file_at_size(os.path.dirname(__file__)+'/icons/flags/' + country_code.lower() + '.svg', 24, 18))

            # Total / max players
            listing[i].append(str(listing[i][server_stat.MASTER_PLAYERCOUNT_COLUMN[-1] - 1]) + '/' + str(listing[i][server_stat.MASTER_PLAYERLIMIT_COLUMN[-1] - 1]))

            treeiter = listmodel.append(listing[i])

    def cb_server_list_selection_changed(self, widget, *data):
        """Updates text in Entry on TreeView selection change."""
        entry = Gtk.Builder.get_object(self.builder, "ServerHost_Entry")

        model, treeiter = widget.get_selected()
        try:
            text = model[treeiter][server_stat.MASTER_HOST_COLUMN[1] - 1]
        except TypeError:
            return

        if text != "SERVER_FULL":
            try:
                Gtk.Entry.set_text(entry, text)
            except TypeError:
                pass


class Settings:
    """Settings main class.
    Contains methods for saving and loading user settings and setting lists.
    """
    def __init__(self, backend, user_settings_file, builder):
        """Loads base variables into the class."""
        self.schema_base_id = 'org.rigsofrods.rigsofrods'

        self.keyfile_config = GLib.KeyFile.new()
        self.keyfile_config.load_from_file(APP_CONFIG, GLib.KeyFileFlags.NONE)

        self.backend = backend
        self.user_settings_file = user_settings_file
        self.builder = builder
        
        if self.backend == "gkeyfile":
            self.keyfile = GLib.KeyFile.new()

            self.keyfile.load_from_file(self.user_settings_file, GLib.KeyFileFlags.NONE)

    def get_groups(self):
        """Compile a list of available settings groups."""
        mapping_cat = []
        for i in range(self.keyfile_config.get_groups()[1]):
            if (GLib.KeyFile.get_value(self.keyfile_config,
                    GLib.KeyFile.get_groups(self.keyfile_config)[0][i], "group")
                    in mapping_cat) == False:

                mapping_cat.append(GLib.KeyFile.get_value(self.keyfile_config,
                    GLib.KeyFile.get_groups(self.keyfile_config)[0][i], "group"))
        return mapping_cat

    def load(self):
        """Settings loading function. Supports GKeyFile and GSettings backends."""

        for i in range(GLib.KeyFile.get_groups(self.keyfile_config)[1]):
            # Define variables
            key = self.keyfile_config.get_groups()[0][i]
            group = self.keyfile_config.get_value(
                self.keyfile_config.get_groups()[0][i], "group")
            widget = Gtk.Builder.get_object(self.builder, self.keyfile_config.get_value(
                self.keyfile_config.get_groups()[0][i], "widget"))

            schema_id = self.schema_base_id + "." + group

            if self.backend == "gsettings":
                # GSettings magic
                gsettings = Gio.Settings.new(schema_id)
                if isinstance(widget, Gtk.Adjustment):
                    value = gsettings.get_int(key)
                elif isinstance(widget, Gtk.CheckButton) or isinstance(widget, Gtk.ToggleButton):
                    value = gsettings.get_boolean(key)
                elif isinstance(widget, Gtk.ComboBoxText) or isinstance(widget, Gtk.Entry):
                    value = gsettings.get_string(key)
            elif self.backend == "gkeyfile":
                try:
                    value = self.keyfile.get_string(group, key)
                except GLib.Error:
                    continue

            if isinstance(widget, Gtk.Adjustment):
                Gtk.Adjustment.set_value(widget, int(value))
            elif isinstance(widget, Gtk.CheckButton) or isinstance(widget, Gtk.ToggleButton):
                try:
                    value = ast.literal_eval(value)
                except ValueError:
                    value = False

                Gtk.ToggleButton.set_active(widget, value)
            elif isinstance(widget, Gtk.ComboBoxText):
                Gtk.ComboBox.set_active_id(widget, str(value))
            elif isinstance(widget, Gtk.Entry):
                Gtk.Entry.set_text(widget, str(value))

    def save(self):
        """Save selected configuration. Supports GKeyFile and GSettings backends."""
        print("\nYour selected configuration:\n--------------")

        for i in range(self.keyfile_config.get_groups()[1]):

            # Define variables
            key = self.keyfile_config.get_groups()[0][i]
            group = self.keyfile_config.get_value(
                self.keyfile_config.get_groups()[0][i], "group")
            widget = Gtk.Builder.get_object(self.builder, self.keyfile_config.get_value(
                self.keyfile_config.get_groups()[0][i], "widget"))

            if isinstance(widget, Gtk.Adjustment):
                value = int(Gtk.Adjustment.get_value(widget))
            elif isinstance(widget, Gtk.CheckButton) or isinstance(widget, Gtk.ToggleButton):
                value = bool(Gtk.ToggleButton.get_active(widget))
            elif isinstance(widget, Gtk.ComboBoxText):
                value = str(Gtk.ComboBox.get_active_id(widget))
            elif isinstance(widget, Gtk.Entry):
                value = str(Gtk.Entry.get_text(widget))

            if self.backend == "gsettings":
                schema_id = self.schema_base_id + "." + group
                gsettings = Gio.Settings.new(schema_id)
                if isinstance(value, bool):
                    gsettings.set_boolean(key, value)
                elif isinstance(value, int):
                    gsettings.set_int(key, value)
                elif isinstance(value, str):
                    gsettings.set_string(key, value)
            elif self.backend == "gkeyfile":
                self.keyfile.set_string(group, key, str(value))

            print(key, "=", value)

        if self.backend == "gkeyfile":
            self.keyfile.save_to_file(self.user_settings_file)


def start_game(path):
    """Start game"""
    from subprocess import call

    try:
        call(os.path.join(path, "RoR"))
    except OSError:
        print("Error launching the game.")

class App:
    """App class."""
    def __init__(self):
        self.builder = Gtk.Builder()
        Gtk.Builder.add_from_file(self.builder, UI_PATH)
    def main(self):
        """Main function.
        Loads the GtkBuilder resources, settings and start the main loop.
        """
        cmd_parser = argparse.ArgumentParser()

        cmd_parser.add_argument("--backend",
                                type=str,
                                choices=["gkeyfile", "gsettings"],
                                default="gkeyfile",
                                help="Defines the storage backend to be used.")

        cmd_parser.add_argument("--profile-path",
                                type=str,
                                default=os.path.normpath(os.path.expanduser(
                                    "~" + os.getlogin() + "/.rigsofrods")),
                                help="Profile path.")

        cmd_parser.add_argument("--config-file",
                                type=str, default="ror.ini", help="Config file name.")

        cmd_parser.add_argument("--ror-path",
                                type=str,
                                default=os.path.dirname(__file__), help="RoR path.")

        self.backend = cmd_parser.parse_args().backend
        self.ror_path = cmd_parser.parse_args().ror_path
        self.user_settings_file = os.path.join(cmd_parser.parse_args().profile_path, "config",
            cmd_parser.parse_args().config_file)

        callbacks = Callbacks(self.backend, self.user_settings_file, self.builder)
        Gtk.Builder.connect_signals(self.builder, callbacks)

        Gtk.Window.show_all(Gtk.Builder.get_object(self.builder, "Configurator_Window"))

        settings = Settings(self.backend, self.user_settings_file, self.builder)
        settings.load()
        callbacks.cb_set_widget_sensitivity()


if __name__ == "__main__":
    app = App()
    app.main()
    Gtk.main()
