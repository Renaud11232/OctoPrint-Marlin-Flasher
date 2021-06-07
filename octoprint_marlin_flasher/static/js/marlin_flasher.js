$(function() {
    function MarlinFlasherViewModel(parameters) {
        var self = this;
        self.settingsViewModel = parameters[0];
        self.loginStateViewModel = parameters[1];

        self.arduinoInstallationLogs = ko.observableArray();
        self.installingArduino = ko.observable(false);

        self.handleArduinoInstallMessage = function(message) {
            $("#marlin_flasher_arduino_install_modal").modal("show");
            self.installingArduino(!message.finished);
            self.arduinoInstallationLogs.push(message.status);
            var pre = $("#marlin_flasher_arduino_install_modal pre")
            pre.scrollTop(pre.prop("scrollHeight"));
            if(message.finished) {
                if(message.success) {
                    self.showSuccess(gettext("Arduino installation"), gettext("The installation was successful"));
                    self.settingsViewModel.settings.plugins.marlin_flasher.arduino.cli_path(message.path);
                } else {
                    self.showErrors(gettext("Arduino installation"), [gettext("The installation failed")]);
                }
            }
        }

        self.installArduino = function() {
            self.arduinoInstallationLogs([]);
            $.ajax({
                type: "POST",
                headers: OctoPrint.getRequestHeaders(),
                url: "/plugin/marlin_flasher/arduino/install"
            }).done(function(data) {
                self.showSuccess(gettext("Arduino installation"), data.message);
            }).fail(function(jqXHR) {
                self.showErrors(gettext("Arduino installation"), jqXHR.responseJSON);
            });
        }

        self.platformioInstallationLogs = ko.observableArray();
        self.installingPlatformio = ko.observable(false);

        self.handlePlatformioInstallMessage = function(message) {
            $("#marlin_flasher_platformio_install_modal").modal("show");
            self.installingPlatformio(!message.finished);
            self.platformioInstallationLogs.push(message.status);
            var pre = $("#marlin_flasher_platformio_install_modal pre")
            pre.scrollTop(pre.prop("scrollHeight"));
            if(message.finished) {
                if(message.success) {
                    self.showSuccess(gettext("Platformio installation"), gettext("The installation was successful"));
                    self.settingsViewModel.settings.plugins.marlin_flasher.platformio.cli_path(message.path);
                } else {
                    self.showErrors(gettext("Platformio installation"), [gettext("The installation failed")]);
                }
            }
        }

        self.installPlatformio = function() {
            self.platformioInstallationLogs([]);
            $.ajax({
                type: "POST",
                headers: OctoPrint.getRequestHeaders(),
                url: "/plugin/marlin_flasher/platformio/install"
            }).done(function(data) {
                self.showSuccess(gettext("Platformio installation"), data.message);
            }).fail(function(jqXHR) {
                self.showErrors(gettext("Platformio installation"), jqXHR.responseJSON);
            });
        }



























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
        self.firmwareVersion = ko.observable();
        self.firmwareAuthor = ko.observable();
        self.uploadTime = ko.observable();
        self.lastFlashOptions = null;

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

        self.showErrors = function(title, errors) {
            new PNotify({
                title: title,
                text: errors.join("\n"),
                type: "error"
            });
        }

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
                self.loadFirmwareInfo();
            },
            error: function(jqXHR, status, error) {
                if(error === "") {
                    self.showError(gettext("Firmware upload failed"), {
                        error: gettext("Check the maximum firmware size")
                    });
                } else {
                    if(jqXHR.responseJSON.error === undefined) {
                        self.showError(gettext("Firmware upload failed"), {
                            error: gettext("The given file was not valid")
                        });
                    } else {
                        self.showError(gettext("Firmware upload failed"), jqXHR.responseJSON);
                    }
                }
                self.uploadProgress(0);
                self.loadFirmwareInfo();
            },
            progress: function(e, data) {
                self.uploadProgress((data.loaded / data.total) * 100);
            }
        }

        self.arduinoFirmwareURL = ko.observable();
        self.downloadingArduinoFirmware = ko.observable(false);

        self.downloadArduinoFirmware = function() {
            self.downloadingArduinoFirmware(true);
            $.ajax({
                type: "POST",
                headers: OctoPrint.getRequestHeaders(),
                url: "/plugin/marlin_flasher/arduino/download_firmware",
                data: {
                    url: self.arduinoFirmwareURL()
                }
            }).done(function(data) {
                self.showSuccess(gettext("Firmware download successful"), data.file);
                self.loadEnvList();
                self.loadFirmwareInfo();
                self.downloadingArduinoFirmware(false);
            }).fail(function(jqXHR) {
                if(jqXHR.responseJSON.error === undefined) {
                    self.showError(gettext("Firmware download failed"), {
                        error: gettext("The URL is not valid")
                    });
                } else {
                    self.showError(gettext("Firmware download failed"), jqXHR.responseJSON);
                }
                self.loadFirmwareInfo();
                self.downloadingArduinoFirmware(false);
            });
        };

        self.platformioFirmwareURL = ko.observable();
        self.downloadingPlatformioFirmware = ko.observable(false);

        self.downloadPlatformioFirmware = function() {
            self.downloadingPlatformioFirmware(true);
            $.ajax({
                type: "POST",
                headers: OctoPrint.getRequestHeaders(),
                url: "/plugin/marlin_flasher/platformio/download_firmware",
                data: {
                    url: self.platformioFirmwareURL()
                }
            }).done(function(data) {
                self.showSuccess(gettext("Firmware download successful"), data.file);
                self.loadEnvList();
                self.loadFirmwareInfo();
                self.downloadingPlatformioFirmware(false);
            }).fail(function(jqXHR) {
                if(jqXHR.responseJSON.error === undefined) {
                    self.showError(gettext("Firmware download failed"), {
                        error: gettext("The URL is not valid")
                    });
                } else {
                    self.showError(gettext("Firmware download failed"), jqXHR.responseJSON);
                }
                self.loadFirmwareInfo();
                self.downloadingPlatformioFirmware(false);
            });
        };

        self.arduinoFirmwareFileButton.fileupload(self.fileUploadParams);
        self.platformioFirmwareFileButton.fileupload(self.fileUploadParams);

        self.loadFirmwareInfo = function() {
            if(self.loginStateViewModel.isAdmin()) {
                $.ajax({
                    type: "GET",
                    headers: OctoPrint.getRequestHeaders(),
                    url: "/plugin/marlin_flasher/firmware"
                }).done(function(data) {
                    self.firmwareVersion(data.version);
                    self.firmwareAuthor(data.author);
                    self.uploadTime(data.upload_time);
                }).fail(function(jqXHR, status, error) {
                    self.showError(gettext("Upload time fetch failed"), jqXHR.responseJSON);
                });
            }
        };

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
            if(self.loginStateViewModel.isAdmin() && self.settingsViewModel.settings.plugins.marlin_flasher.platform_type() === "arduino") {
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
                    $.ajax({
                        type: "GET",
                        headers: OctoPrint.getRequestHeaders(),
                        url: "/plugin/marlin_flasher/last_flash_options",
                    }).done(function (data) {
                        if(data) {
                            self.lastFlashOptions = data;
                            self.selectedBoard(data.fqbn);
                        }
                    });
                }).fail(function(jqXHR, status, error) {
                    self.showError(gettext("Board list fetch failed"), jqXHR.responseJSON);
                });
            }
        };
        self.loadEnvList = function() {
            if(self.loginStateViewModel.isAdmin() && self.settingsViewModel.settings.plugins.marlin_flasher.platform_type() === "platform_io") {
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
                    $.ajax({
                        type: "GET",
                        headers: OctoPrint.getRequestHeaders(),
                        url: "/plugin/marlin_flasher/last_flash_options",
                    }).done(function (data) {
                        if(data && data.env) {
                            self.lastFlashOptions = data;
                            self.selectedEnv(data.env);
                        }
                    });
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
                    if(self.lastFlashOptions) {
                        for(var key in self.lastFlashOptions) {
                            if(key !== "fqbn") {
                                $("#flash form select[name=" + key + "]").val(self.lastFlashOptions[key]);
                            }
                        }
                        self.lastFlashOptions = null;
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
            self.loadFirmwareInfo();
        };
        self.onDataUpdaterPluginMessage = function(plugin, message) {
            if(plugin === "marlin_flasher" && self.loginStateViewModel.isAdmin()) {
                if(message.type === "flash_progress") {
                    self.progressStep(message.step);
                    self.flashingProgress(message.progress);
                } else if(message.type === "settings_saved") {
                    self.loadBoardList();
                    self.loadEnvList();
                    self.loadFirmwareInfo();
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
                    self.loadFirmwareInfo();
                } else if (message.type === "arduino_install") {
                    self.handleArduinoInstallMessage(message);
                } else if (message.type === "platformio_install") {
                    self.handlePlatformioInstallMessage(message);
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
            if(self.settingsViewModel.settings.plugins.marlin_flasher.pre_flash_script() === "") {
                self.settingsViewModel.settings.plugins.marlin_flasher.pre_flash_script(null);
            }
            if(self.settingsViewModel.settings.plugins.marlin_flasher.post_flash_script() === "") {
                self.settingsViewModel.settings.plugins.marlin_flasher.post_flash_script(null);
            }
            if(self.settingsViewModel.settings.plugins.marlin_flasher.pre_flash_delay() === "") {
                self.settingsViewModel.settings.plugins.marlin_flasher.pre_flash_delay("0");
            }
            self.settingsViewModel.settings.plugins.marlin_flasher.pre_flash_delay(parseInt(self.settingsViewModel.settings.plugins.marlin_flasher.pre_flash_delay()));
            if(self.settingsViewModel.settings.plugins.marlin_flasher.post_flash_delay() === "") {
                self.settingsViewModel.settings.plugins.marlin_flasher.post_flash_delay("0");
            }
            self.settingsViewModel.settings.plugins.marlin_flasher.post_flash_delay(parseInt(self.settingsViewModel.settings.plugins.marlin_flasher.post_flash_delay()));
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
            "#marlin_flasher_modal",
            "#marlin_flasher_arduino_install_modal",
            "#marlin_flasher_platformio_install_modal"
        ]
    });
});
