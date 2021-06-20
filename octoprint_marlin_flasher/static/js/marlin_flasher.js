$(function() {
    function MarlinFlasherViewModel(parameters) {
        var self = this;
        self.settingsViewModel = parameters[0];
        self.loginStateViewModel = parameters[1];

        //////////////////////////////////////////////////////////////////////////////
        // Common
        //////////////////////////////////////////////////////////////////////////////

        self.firmwareVersion = ko.observable();
        self.firmwareAuthor = ko.observable();
        self.uploadTime = ko.observable();

        self.handleFirmwareInfo = function(message) {
            self.firmwareVersion(message.version);
            self.firmwareAuthor(message.author);
            self.uploadTime(message.upload_time);
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

        self.uploadProgress = ko.observable(0);

        self.fileUploadParams = {
            maxNumberOfFiles: 1,
            headers: OctoPrint.getRequestHeaders(),
            done: function(e, data) {
                self.showSuccess(gettext("Firmware upload successful"), data.result.file);
            },
            error: function(jqXHR, status, error) {
                if(error === "") {
                    self.showErrors(gettext("Firmware upload failed"), [gettext("Check the maximum firmware size")]);
                } else {
                    self.showErrors(gettext("Firmware upload failed"), jqXHR.responseJSON);
                }
                self.uploadProgress(0);
            },
            progress: function(e, data) {
                self.uploadProgress((data.loaded / data.total) * 100);
            }
        };

        self.onAllBound = function() {
            $("#arduino_firmware_file").fileupload(self.fileUploadParams);
            $("#platformio_firmware_file").fileupload(self.fileUploadParams);
        };

        self.onDataUpdaterPluginMessage = function(plugin, message) {
            if(plugin === "marlin_flasher" && self.loginStateViewModel.isAdmin()) {
                if (message.type === "arduino_install") {
                    self.handleArduinoInstallMessage(message);
                } else if (message.type === "platformio_install") {
                    self.handlePlatformioInstallMessage(message);
                } else if (message.type === "firmware_info") {
                    self.handleFirmwareInfo(message);
                } else if (message.type === "arduino_boards") {
                    self.handleArduinoBoards(message);
                } else if (message.type === "arduino_flash_status") {
                    self.handleArduinoFlashStatus(message);
                }
            }
        };

        self.stderr = ko.observable();

        self.showCompilationError = function(stderr) {
            self.stderr(stderr);
            $("#marlin_flasher_modal").modal("show");
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

        //////////////////////////////////////////////////////////////////////////////
        // Arduino
        //////////////////////////////////////////////////////////////////////////////

        self.boardList = ko.observableArray();
        self.arduinoInstallationLogs = ko.observableArray();
        self.installingArduino = ko.observable(false);
        self.arduinoFirmwareURL = ko.observable();
        self.downloadingArduinoFirmware = ko.observable(false);
        self.coreSearchResult = ko.observableArray();
        self.libSearchResult = ko.observableArray();
        self.selectedBoard = ko.observable();
        self.boardOptions = ko.observableArray();
        self.boardOptionsLoading = ko.observable(false);

        self.handleArduinoBoards = function(message) {
            if(message.result.boards) {
                self.boardList(message.result.boards);
            } else {
                self.boardList([]);
            }
        };

        self.selectedBoard.subscribe(function(newValue) {
            self.boardOptions([]);
            if (newValue) {
                self.boardOptionsLoading(true);
                $.ajax({
                    type: "GET",
                    headers: OctoPrint.getRequestHeaders(),
                    url: "/plugin/marlin_flasher/arduino/board/details",
                    data: {
                        fqbn: newValue
                    }
                }).done(function (data) {
                    if(data) {
                        self.boardOptions(data.config_options);
                    }
                }).fail(function(jqXHR) {
                    self.showErrors(gettext("Board option fetch failed"), jqXHR.responseJSON);
                }).always(function() {
                    self.boardOptionsLoading(false);
                });
            }
        });

        self.boardOptions.subscribe(function(newValue) {
            if(newValue) {
                for (var option = 0; option < newValue.length; option++) {
                    for (var value = 0; value < newValue[option].values.length; value++) {
                        if(newValue[option].values[value].selected) {
                            $('select[name="' + newValue[option].option + '"]').val(newValue[option].values[value].value);
                        }
                    }
                }
            }
        });

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
            }).fail(function(jqXHR) {
                self.showErrors(gettext("Firmware download failed"), jqXHR.responseJSON);
            }).always(function() {
                self.downloadingArduinoFirmware(false);
            });
        };

        self.searchCore = function(form) {
            $("#search-core-btn").button("loading");
            $.ajax({
                type: "GET",
                headers: OctoPrint.getRequestHeaders(),
                url: "/plugin/marlin_flasher/arduino/cores/search",
                data: $(form).serialize()
            }).done(function (data) {
                self.coreSearchResult(data);
            }).fail(function(jqXHR) {
                self.showErrors(gettext("Core search failed"), jqXHR.responseJSON);
            }).always(function() {
                $("#search-core-btn").button("reset");
            });
        };

        self.installCore = function(data, event) {
            $(event.currentTarget).hide();
            var loader = $("<i>").addClass("fas").addClass("fa-spin").addClass("fa-spinner").addClass("fa-2x");
            $(event.currentTarget).after(loader);
            $.ajax({
                type: "POST",
                headers: OctoPrint.getRequestHeaders(),
                url: "/plugin/marlin_flasher/arduino/cores/install",
                data: {
                    core: data.id
                }
            }).done(function(data) {
                self.showSuccess(gettext("Core install successful"), gettext("Successfully installed {core}").replace("{core}", data.core));
            }).fail(function(jqXHR) {
                self.showErrors(gettext("Core install failed"), jqXHR.responseJSON);
            }).always(function() {
                loader.remove();
                $(event.currentTarget).show();
            });
        };

        self.uninstallCore = function(data, event) {
            $(event.currentTarget).hide();
            var loader = $("<i>").addClass("fas").addClass("fa-spin").addClass("fa-spinner").addClass("fa-2x");
            $(event.currentTarget).after(loader);
            $.ajax({
                type: "POST",
                headers: OctoPrint.getRequestHeaders(),
                url: "/plugin/marlin_flasher/arduino/cores/uninstall",
                data: {
                    core: data.id
                }
            }).done(function(data) {
                self.showSuccess(gettext("Core uninstall successful"), gettext("Successfully uninstalled {core}").replace("{core}", data.core));
            }).fail(function(jqXHR) {
                self.showErrors(gettext("Core uninstall failed"), jqXHR.responseJSON);
            }).always(function() {
                loader.remove();
                $(event.currentTarget).show();
            });
        };

        self.searchLib = function(form) {
            $("#search-lib-btn").button("loading");
            $.ajax({
                type: "GET",
                headers: OctoPrint.getRequestHeaders(),
                url: "/plugin/marlin_flasher/arduino/libs/search",
                data: $(form).serialize()
            }).done(function (data) {
                if(data.hasOwnProperty("libraries")) {
                    self.libSearchResult(data.libraries);
                } else {
                    self.libSearchResult([]);
                }
            }).fail(function(jqXHR) {
                self.showErrors(gettext("Lib search failed"), jqXHR.responseJSON);
            }).always(function() {
                $("#search-lib-btn").button("reset");
            });
        };

        self.installLib = function(data, event) {
            $(event.currentTarget).hide();
            var loader = $("<i>").addClass("fas").addClass("fa-spin").addClass("fa-spinner").addClass("fa-2x");
            $(event.currentTarget).after(loader);
            $.ajax({
                type: "POST",
                headers: OctoPrint.getRequestHeaders(),
                url: "/plugin/marlin_flasher/arduino/libs/install",
                data: {
                    lib: data.name
                }
            }).done(function(data) {
                self.showSuccess(gettext("Lib install successful"), gettext("Successfully installed {lib}").replace("{lib}", data.lib));
            }).fail(function(jqXHR) {
                self.showErrors(gettext("Lib install failed"), jqXHR.responseJSON);
            }).always(function() {
                loader.remove();
                $(event.currentTarget).show();
            });
        };

        self.uninstallLib =  function(data, event) {
            $(event.currentTarget).hide();
            var loader = $("<i>").addClass("fas").addClass("fa-spin").addClass("fa-spinner").addClass("fa-2x");
            $(event.currentTarget).after(loader);
            $.ajax({
                type: "POST",
                headers: OctoPrint.getRequestHeaders(),
                url: "/plugin/marlin_flasher/arduino/libs/uninstall",
                data: {
                    lib: data.name
                }
            }).done(function(data) {
                self.showSuccess(gettext("Lib uninstall successful"), gettext("Successfully uninstalled {lib}").replace("{lib}", data.lib));
            }).fail(function(jqXHR) {
                self.showErrors(gettext("Lib uninstall failed"), jqXHR.responseJSON);
            }).always(function() {
                loader.remove();
                $(event.currentTarget).show();
            });
        };

        self.flashArduino = function(form) {
            $("#arduino_flash-button").button("loading");
            $.ajax({
                type: "POST",
                headers: OctoPrint.getRequestHeaders(),
                url: "/plugin/marlin_flasher/arduino/flash",
                data: $(form).serialize()
            }).fail(function(jqXHR) {
                self.showErrors(gettext("Flashing failed to start"), jqXHR.responseJSON);
                $("#arduino_flash-button").button("reset");
            });
        };

        self.arduinoFlashStep = ko.observable();
        self.arduinoFlashProgress = ko.observable();
        self.arduinoFlashFinished = ko.observable();
        self.arduinoFlashSucess = ko.observable();

        self.handleArduinoFlashStatus = function(message) {
            this.arduinoFlashStep(message.step_name);
            this.arduinoFlashProgress(message.progress);
            this.arduinoFlashFinished(message.finished);
            this.arduinoFlashSucess(message.success);
            if(message.finished) {
                $("#arduino_flash-button").button("reset");
                if(!message.success) {
                    self.showErrors(gettext("Flashing failed"), [message.message]);
                    self.showCompilationError(message.error_output);
                }
            }
        };

        //////////////////////////////////////////////////////////////////////////////
        // PlatformIO
        //////////////////////////////////////////////////////////////////////////////

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
            }).fail(function(jqXHR) {
                self.showErrors(gettext("Firmware download failed"), jqXHR.responseJSON);
            }).always(function() {
                self.downloadingPlatformioFirmware(false);
            });
        };

        self.platformioFlashStep = ko.observable();
        self.platformioFlashProgress = ko.observable();
        self.platformioFlashFinished = ko.observable();
        self.platformioFlashSucess = ko.observable();

        self.flashPlatformIO = function(form) {
            $("#platformio_flash-button").button("loading");
            $.ajax({
                type: "POST",
                headers: OctoPrint.getRequestHeaders(),
                url: "/plugin/marlin_flasher/flash",
                data: $(form).serialize()
            }).fail(function(jqXHR) {
                self.showErrors(gettext("Flashing failed to start"), jqXHR.responseJSON);
                $("#platformio_flash-button").button("reset");
            });
        };





        self.envList = ko.observableArray([]);
        self.selectedEnv = ko.observable();
        self.envListLoading = ko.observable(false);
        self.lastFlashOptions = null;

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
