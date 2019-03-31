$(function() {
    function MarlinFlasherViewModel(parameters) {
        var self = this;
        self.settingsViewModel = parameters[0];
        self.loginStateViewModel = parameters[1];
        self.sketchFileButton = $("#sketch_file");
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

        self.sketchFileButton.fileupload({
            maxNumberOfFiles: 1,
            headers: OctoPrint.getRequestHeaders(),
            done: function(e, data) {
                new PNotify({
                    title: gettext("Sketch upload successful"),
                    text: data.result.ino,
                    type: "success"
                });
                self.uploadProgress(0);
            },
            error: function(jqXHR, status, error) {
                if(error === "") {
                    new PNotify({
                        title: gettext("Sketch upload failed"),
                        text: gettext("Check the maximum sketch size"),
                        type: "error"
                    });
                } else {
                    new PNotify({
                        title: gettext("Sketch upload failed"),
                        text: jqXHR.responseJSON.message,
                        type: "error"
                    });
                }
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
                if(data.hasOwnProperty("Platforms")) {
                    self.coreSearchResult(data.Platforms);
                } else {
                    self.coreSearchResult([]);
                }
            }).fail(function(jqXHR, status, error) {
                new PNotify({
                    title: gettext("Core search failed"),
                    text: jqXHR.responseJSON.message,
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
                    text: jqXHR.responseJSON.message,
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
                    text: jqXHR.responseJSON.message,
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
                    text: jqXHR.responseJSON.message,
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
                    lib: data.Name
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
                    text: jqXHR.responseJSON.message,
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
                    lib: data.Name
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
                    text: jqXHR.responseJSON.message,
                    type: "error"
                });
            }).always(function() {
                $(event.currentTarget).button("reset");
            });
        };
        self.loadBoardList = function() {
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
                    text: jqXHR.responseJSON.message,
                    type: "error"
                });
            });
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
                    text: jqXHR.responseJSON.message,
                    type: "error"
                });
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
                        self.boardOptions(data.ConfigOptions);
                    }
                }).fail(function(jqXHR, status, error) {
                    new PNotify({
                        title: gettext("Board option fetch failed"),
                        text: jqXHR.responseJSON.message,
                        type: "error"
                    });
                });
            }
        });
        self.onAllBound = function(viewModels) {
            if(self.loginStateViewModel.isAdmin()) {
                self.loadBoardList();
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
