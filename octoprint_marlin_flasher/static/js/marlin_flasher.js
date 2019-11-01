$(function() {
    function MarlinFlasherViewModel(parameters) {
        var self = this;
        self.settingsViewModel = parameters[0];
        self.loginStateViewModel = parameters[1];
        self.firmwareFileButton = $("#firmware_file");
        self.flashButton = $("#flash-button");
        self.searchCoreButton = $("#search-core-btn");
        self.searchLibButton = $("#search-lib-btn");
        self.stderrModal = $("#marlin_flasher_modal");

        self.coreSearchResult = ko.observableArray();
        self.libSearchResult = ko.observableArray();
        self.boardList = ko.observableArray();
        self.selectedBoard = ko.observable();
        self.boardOptions = ko.observableArray();
        self.stderr = ko.observable();
        self.uploadProgress = ko.observable(0);
        self.flashingProgress = ko.observable(0);
        self.progressStep = ko.observable();
        self.selectedPlatform = ko.observable();

        self.firmwareFileButton.fileupload({
            maxNumberOfFiles: 1,
            headers: OctoPrint.getRequestHeaders(),
            done: function(e, data) {
                new PNotify({
                    title: gettext("Firmware upload successful"),
                    text: data.result.file,
                    type: "success"
                });
                self.uploadProgress(0);
            },
            error: function(jqXHR, status, error) {
                if(error === "") {
                    new PNotify({
                        title: gettext("Firmware upload failed"),
                        text: gettext("Check the maximum firmware size"),
                        type: "error"
                    });
                } else {
                    if(typeof jqXHR.responseJSON.error === "undefined") {
                        new PNotify({
                            title: gettext("Firmware upload failed"),
                            text: gettext("The given file was not valid"),
                            type: "error"
                        });
                    } else {
                        new PNotify({
                            title: gettext("Firmware upload failed"),
                            text: jqXHR.responseJSON.error,
                            type: "error"
                        });
                    }
                };
                self.uploadProgress(0);
            },
            progress: function(e, data) {
                self.uploadProgress((data.loaded / data.total) * 100);
            }
        });
        self.searchCore = function(form) {
            self.searchCoreButton.button("loading");
            $.ajax({
                type: "GET",
                headers: OctoPrint.getRequestHeaders(),
                url: "/plugin/marlin_flasher/cores/search",
                data: $(form).serialize()
            }).done(function (data) {
                self.coreSearchResult(data);
            }).fail(function(jqXHR, status, error) {
                new PNotify({
                    title: gettext("Core search failed"),
                    text: jqXHR.responseJSON.error,
                    type: "error"
                });
            }).always(function() {
                self.searchCoreButton.button("reset");
            });
        };
        self.installCore = function(data, event) {
            $(event.currentTarget).button("loading");
            $.ajax({
                type: "POST",
                headers: OctoPrint.getRequestHeaders(),
                url: "/plugin/marlin_flasher/cores/install",
                data: {
                    core: data.ID
                }
            }).done(function(data) {
                self.loadBoardList();
                new PNotify({
                    title: gettext("Core install successful"),
                    text: gettext("Successfully installed {core}").replace("{core}", data.core),
                    type: "success"
                });
            }).fail(function(jqXHR, status, error) {
                new PNotify({
                    title: gettext("Core install failed"),
                    text: jqXHR.responseJSON.error,
                    type: "error"
                });
            }).always(function() {
                $(event.currentTarget).button("reset");
            });
        };
        self.uninstallCore = function(data, event) {
            $(event.currentTarget).button("loading");
            $.ajax({
                type: "POST",
                headers: OctoPrint.getRequestHeaders(),
                url: "/plugin/marlin_flasher/cores/uninstall",
                data: {
                    core: data.ID
                }
            }).done(function(data) {
                self.loadBoardList();
                new PNotify({
                    title: gettext("Core uninstall successful"),
                    text: gettext("Successfully uninstalled {core}").replace("{core}", data.core),
                    type: "success"
                });
            }).fail(function(jqXHR, status, error) {
                new PNotify({
                    title: gettext("Core uninstall failed"),
                    text: jqXHR.responseJSON.error,
                    type: "error"
                });
            }).always(function() {
                $(event.currentTarget).button("reset");
            });
        };
        self.searchLib = function(form) {
            self.searchLibButton.button("loading");
            $.ajax({
                type: "GET",
                headers: OctoPrint.getRequestHeaders(),
                url: "/plugin/marlin_flasher/libs/search",
                data: $(form).serialize()
            }).done(function (data) {
                if(data.hasOwnProperty("libraries")) {
                    self.libSearchResult(data.libraries);
                } else {
                    self.libSearchResult([]);
                }
            }).fail(function(jqXHR, status, error) {
                new PNotify({
                    title: gettext("Lib search failed"),
                    text: jqXHR.responseJSON.error,
                    type: "error"
                });
            }).always(function() {
                self.searchLibButton.button("reset");
            });
        };
        self.installLib = function(data, event) {
            $(event.currentTarget).button("loading");
            $.ajax({
                type: "POST",
                headers: OctoPrint.getRequestHeaders(),
                url: "/plugin/marlin_flasher/libs/install",
                data: {
                    lib: data.name
                }
            }).done(function(data) {
                new PNotify({
                    title: gettext("Lib install successful"),
                    text: gettext("Successfully installed {lib}").replace("{lib}", data.lib),
                    type: "success"
                });
            }).fail(function(jqXHR, status, error) {
                new PNotify({
                    title: gettext("Lib install failed"),
                    text: jqXHR.responseJSON.error,
                    type: "error"
                });
            }).always(function() {
                $(event.currentTarget).button("reset");
            });
        };
        self.uninstallLib =  function(data, event) {
            $(event.currentTarget).button("loading");
            $.ajax({
                type: "POST",
                headers: OctoPrint.getRequestHeaders(),
                url: "/plugin/marlin_flasher/libs/uninstall",
                data: {
                    lib: data.name
                }
            }).done(function(data) {
                new PNotify({
                    title: gettext("Lib uninstall successful"),
                    text: gettext("Successfully uninstalled {lib}").replace("{lib}", data.lib),
                    type: "success"
                });
            }).fail(function(jqXHR, status, error) {
                new PNotify({
                    title: gettext("Lib uninstall failed"),
                    text: jqXHR.responseJSON.error,
                    type: "error"
                });
            }).always(function() {
                $(event.currentTarget).button("reset");
            });
        };
        self.loadBoardList = function() {
            if(self.loginStateViewModel.isAdmin() && self.settingsViewModel.settings.plugins.marlin_flasher.platform_type() == 0) {
                $.ajax({
                    type: "GET",
                    headers: OctoPrint.getRequestHeaders(),
                    url: "/plugin/marlin_flasher/board/listall",
                }).done(function (data) {
                    if(data.boards) {
                        self.boardList(data.boards);
                    } else {
                        self.boardList([]);
                    }
                }).fail(function(jqXHR, status, error) {
                    new PNotify({
                        title: gettext("Board list fetch failed"),
                        text: jqXHR.responseJSON.error,
                        type: "error"
                    });
                });
            }
        };
        self.flash = function(form) {
            self.flashButton.button("loading");
            $.ajax({
                type: "POST",
                headers: OctoPrint.getRequestHeaders(),
                url: "/plugin/marlin_flasher/flash",
                data: $(form).serialize()
            }).done(function (data) {
                new PNotify({
                    title: gettext("Flashing successful"),
                    text: data.message,
                    type: "success"
                });
            }).fail(function(jqXHR, status, error) {
                new PNotify({
                    title: gettext("Flashing failed"),
                    text: jqXHR.responseJSON.error,
                    type: "error"
                });
                self.progressStep(null);
                self.flashingProgress(0);
                if(jqXHR.responseJSON.stderr) {
                    self.stderr(jqXHR.responseJSON.stderr);
                    self.stderrModal.modal("show");
                } else {
                    self.stderr(null);
                }
            }).always(function() {
                self.flashButton.button("reset");
            });
        };
        self.selectedBoard.subscribe(function(newValue) {
            self.boardOptions([]);
            if (newValue) {
                $.ajax({
                    type: "GET",
                    headers: OctoPrint.getRequestHeaders(),
                    url: "/plugin/marlin_flasher/board/details",
                    data: {
                        fqbn: newValue
                    }
                }).done(function (data) {
                    if(data) {
                        self.boardOptions(data.config_options);
                    }
                }).fail(function(jqXHR, status, error) {
                    new PNotify({
                        title: gettext("Board option fetch failed"),
                        text: jqXHR.responseJSON.error,
                        type: "error"
                    });
                });
            }
        });
        self.onAllBound = function(viewModels) {
            self.selectedPlatform(self.settingsViewModel.settings.plugins.marlin_flasher.platform_type() + "");
            self.settingsViewModel.settings.plugins.marlin_flasher.platform_type.subscribe(function(value) {
                self.selectedPlatform(value + "");
            });
            self.loadBoardList();
        };
        self.onDataUpdaterPluginMessage = function(plugin, message) {
            if(plugin == "marlin_flasher") {
                if(message.type === "flash_progress") {
                    self.progressStep(message.step);
                    self.flashingProgress(message.progress);
                } else if(message.type === "settings_saved") {
                    self.loadBoardList();
                }
            }
        };
        self.onSettingsBeforeSave = function() {
            self.settingsViewModel.settings.plugins.marlin_flasher.max_upload_size(parseInt(self.settingsViewModel.settings.plugins.marlin_flasher.max_upload_size()));
            self.settingsViewModel.settings.plugins.marlin_flasher.platform_type(parseInt(self.selectedPlatform()));
            if(self.settingsViewModel.settings.plugins.marlin_flasher.arduino.additional_urls() === "") {
                self.settingsViewModel.settings.plugins.marlin_flasher.arduino.additional_urls(null);
            }
            if(self.settingsViewModel.settings.plugins.marlin_flasher.arduino.cli_path() === "") {
                self.settingsViewModel.settings.plugins.marlin_flasher.arduino.cli_path(null);
            }
        };
    }

    OCTOPRINT_VIEWMODELS.push({
        construct: MarlinFlasherViewModel,
        dependencies: [
            "settingsViewModel",
            "loginStateViewModel"
        ],
        elements: [
            "#settings_plugin_marlin_flasher",
            "#wizard_plugin_marlin_flasher",
            "#tab_plugin_marlin_flasher",
            "#marlin_flasher_modal"
        ]
    });
});
