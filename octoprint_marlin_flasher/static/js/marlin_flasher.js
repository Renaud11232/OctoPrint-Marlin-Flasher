$(function() {
    function MarlinFlasherViewModel(parameters) {
        var self = this;
        self.settingsViewModel = parameters[0];
        self.loginStateViewModel = parameters[1];
        self.arduinoFirmwareFileButton = $("#arduino_firmware_file");
        self.platformioFirmwareFileButton = $("#platformio_firmware_file");
        self.arduinoFlashButton = $("#arduino_flash-button");
        self.platformioFlashButton = $("#platformio_flash-button");
        self.searchCoreButton = $("#search-core-btn");
        self.searchLibButton = $("#search-lib-btn");
        self.stderrModal = $("#marlin_flasher_modal");

        self.coreSearchResult = ko.observableArray();
        self.libSearchResult = ko.observableArray();
        self.boardList = ko.observableArray();
        self.selectedBoard = ko.observable();
        self.envList = ko.observableArray([]);
        self.selectedEnv = ko.observable();
        self.envListLoading = ko.observable(false);
        self.boardOptions = ko.observableArray();
        self.stderr = ko.observable();
        self.uploadProgress = ko.observable(0);
        self.flashingProgress = ko.observable(0);
        self.progressStep = ko.observable();
        self.flashButtonEnabled = ko.observable(false);
        self.boardOptionsLoading = ko.observable(false);

        self.showError = function(title, errorData) {
            var text = "";
            if(errorData.error) {
                text = errorData.error;
            }
            if(errorData.cause) {
                if(text) {
                    text += "\n";
                }
                text += gettext("Cause : ") + errorData.cause;
            }
            new PNotify({
                title: title,
                text: text,
                type: "error"
            });
            if(errorData.stderr) {
                self.stderr(errorData.stderr);
                self.stderrModal.modal("show");
            }
        };

        self.showSuccess = function(title, text) {
            new PNotify({
                title: title,
                text: text,
                type: "success"
            });
        }

        self.fileUploadParams = {
            maxNumberOfFiles: 1,
            headers: OctoPrint.getRequestHeaders(),
            done: function(e, data) {
                self.showSuccess(gettext("Firmware upload successful"), data.result.file);
                self.uploadProgress(0);
                self.loadEnvList();
            },
            error: function(jqXHR, status, error) {
                if(error === "") {
                    self.showError(gettext("Firmware upload failed"), {
                        error: gettext("Check the maximum firmware size")
                    });
                } else {
                    if(typeof jqXHR.responseJSON.error === "undefined") {
                        self.showError(gettext("Firmware upload failed"), {
                            error: gettext("The given file was not valid")
                        });
                    } else {
                        self.showError(gettext("Firmware upload failed"), jqXHR.responseJSON);
                    }
                };
                self.uploadProgress(0);
            },
            progress: function(e, data) {
                self.uploadProgress((data.loaded / data.total) * 100);
            }
        }

        self.arduinoFirmwareFileButton.fileupload(self.fileUploadParams);
        self.platformioFirmwareFileButton.fileupload(self.fileUploadParams);
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
                self.showError(gettext("Core search failed"), jqXHR.responseJSON);
            }).always(function() {
                self.searchCoreButton.button("reset");
            });
        };
        self.installCore = function(data, event) {
            $(event.currentTarget).hide();
            var loader = $("<div>").addClass("loader").addClass("loader-centered").addClass("loader-install");
            $(event.currentTarget).after(loader);
            $.ajax({
                type: "POST",
                headers: OctoPrint.getRequestHeaders(),
                url: "/plugin/marlin_flasher/cores/install",
                data: {
                    core: data.ID
                }
            }).done(function(data) {
                self.loadBoardList();
                self.showSuccess(gettext("Core install successful"), gettext("Successfully installed {core}").replace("{core}", data.core));
            }).fail(function(jqXHR, status, error) {
                self.showError(gettext("Core install failed"), jqXHR.responseJSON);
            }).always(function() {
                loader.remove();
                $(event.currentTarget).show();
            });
        };
        self.uninstallCore = function(data, event) {
            $(event.currentTarget).hide();
            var loader = $("<div>").addClass("loader").addClass("loader-centered").addClass("loader-uninstall");
            $(event.currentTarget).after(loader);
            $.ajax({
                type: "POST",
                headers: OctoPrint.getRequestHeaders(),
                url: "/plugin/marlin_flasher/cores/uninstall",
                data: {
                    core: data.ID
                }
            }).done(function(data) {
                self.loadBoardList();
                self.showSuccess(gettext("Core uninstall successful"), gettext("Successfully uninstalled {core}").replace("{core}", data.core));
            }).fail(function(jqXHR, status, error) {
                self.showError(gettext("Core uninstall failed"), jqXHR.responseJSON);
            }).always(function() {
                loader.remove();
                $(event.currentTarget).show();
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
                self.showError(gettext("Lib search failed"), jqXHR.responseJSON);
            }).always(function() {
                self.searchLibButton.button("reset");
            });
        };
        self.installLib = function(data, event) {
            $(event.currentTarget).hide();
            var loader = $("<div>").addClass("loader").addClass("loader-centered").addClass("loader-install");
            $(event.currentTarget).after(loader);
            $.ajax({
                type: "POST",
                headers: OctoPrint.getRequestHeaders(),
                url: "/plugin/marlin_flasher/libs/install",
                data: {
                    lib: data.name
                }
            }).done(function(data) {
                self.showSuccess(gettext("Lib install successful"), gettext("Successfully installed {lib}").replace("{lib}", data.lib));
            }).fail(function(jqXHR, status, error) {
                self.showError(gettext("Lib install failed"), jqXHR.responseJSON);
            }).always(function() {
                loader.remove();
                $(event.currentTarget).show();
            });
        };
        self.uninstallLib =  function(data, event) {
            $(event.currentTarget).hide();
            var loader = $("<div>").addClass("loader").addClass("loader-centered").addClass("loader-uninstall");
            $(event.currentTarget).after(loader);
            $.ajax({
                type: "POST",
                headers: OctoPrint.getRequestHeaders(),
                url: "/plugin/marlin_flasher/libs/uninstall",
                data: {
                    lib: data.name
                }
            }).done(function(data) {
                self.showSuccess(gettext("Lib uninstall successful"), gettext("Successfully uninstalled {lib}").replace("{lib}", data.lib));
            }).fail(function(jqXHR, status, error) {
                self.showError(gettext("Lib uninstall failed"), jqXHR.responseJSON);
            }).always(function() {
                loader.remove();
                $(event.currentTarget).show();
            });
        };
        self.loadBoardList = function() {
            if(self.loginStateViewModel.isAdmin() && self.settingsViewModel.settings.plugins.marlin_flasher.platform_type() == "arduino") {
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
                    self.showError(gettext("Board list fetch failed"), jqXHR.responseJSON);
                });
            }
        };
        self.loadEnvList = function() {
            if(self.loginStateViewModel.isAdmin() && self.settingsViewModel.settings.plugins.marlin_flasher.platform_type() == "platform_io") {
                self.envList([]);
                self.envListLoading(true);
                $.ajax({
                    type: "GET",
                    headers: OctoPrint.getRequestHeaders(),
                    url: "/plugin/marlin_flasher/board/details",
                }).done(function (data) {
                    if(data) {
                        self.envList(data);
                        if(data.length === 1) {
                            self.selectedEnv(data[0]);
                        }
                    }
                }).always(function() {
                    self.envListLoading(false);
                });
            }
        };
        self.flash = function(form) {
            self.arduinoFlashButton.button("loading");
            self.platformioFlashButton.button("loading");
            $.ajax({
                type: "POST",
                headers: OctoPrint.getRequestHeaders(),
                url: "/plugin/marlin_flasher/flash",
                data: $(form).serialize()
            }).fail(function(jqXHR, status, error) {
                self.showError(gettext("Flashing failed to start"), jqXHR.responseJSON);
                self.arduinoFlashButton.button("reset");
                self.platformioFlashButton.button("reset");
            });
        };
        self.selectedBoard.subscribe(function(newValue) {
            self.boardOptions([]);
            self.flashButtonEnabled(false);
            if (newValue) {
                self.boardOptionsLoading(true);
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
                    self.flashButtonEnabled(true);
                }).fail(function(jqXHR, status, error) {
                    self.showError(gettext("Board option fetch failed"), jqXHR.responseJSON);
                }).always(function() {
                    self.boardOptionsLoading(false);
                });
            }
        });
        self.onAllBound = function(viewModels) {
            self.loadBoardList();
            self.loadEnvList();
        };
        self.onDataUpdaterPluginMessage = function(plugin, message) {
            if(plugin == "marlin_flasher") {
                if(message.type === "flash_progress") {
                    self.progressStep(message.step);
                    self.flashingProgress(message.progress);
                } else if(message.type === "settings_saved") {
                    self.loadBoardList();
                    self.loadEnvList();
                } else if(message.type === "flash_result") {
                    if(message.success) {
                        self.showSuccess(gettext("Flashing successful"), message.message);
                    } else {
                        self.showError(gettext("Flashing failed"), message);
                        self.progressStep(null);
                        self.flashingProgress(0);
                    }
                    self.arduinoFlashButton.button("reset");
                    self.platformioFlashButton.button("reset");
                }
            }
        };
        self.onSettingsBeforeSave = function() {
            self.settingsViewModel.settings.plugins.marlin_flasher.max_upload_size(parseInt(self.settingsViewModel.settings.plugins.marlin_flasher.max_upload_size()));
            if(self.settingsViewModel.settings.plugins.marlin_flasher.arduino.additional_urls() === "") {
                self.settingsViewModel.settings.plugins.marlin_flasher.arduino.additional_urls(null);
            }
            if(self.settingsViewModel.settings.plugins.marlin_flasher.arduino.cli_path() === "") {
                self.settingsViewModel.settings.plugins.marlin_flasher.arduino.cli_path(null);
            }
            if(self.settingsViewModel.settings.plugins.marlin_flasher.platformio.cli_path() === "") {
                self.settingsViewModel.settings.plugins.marlin_flasher.platformio.cli_path(null);
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
