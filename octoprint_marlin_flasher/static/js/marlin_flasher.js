$(function() {
    function MarlinFlasherViewModel(parameters) {
        var self = this;
        self.settingsViewModel = parameters[0];
        self.sketchFileButton = $("#sketch_file");
        self.coreSearchTextField = $("#cores-search-text");
        self.libSearchTextField = $("#libs-search-text");
        self.flashOptionContainer = $("#flash-options");
        self.fqbn = $("#fqbn");
        self.flashForm = $("#form-flash");
        self.flashButton = $("#flash-button");

        self.coreSearchResult = ko.observableArray();
        self.libSearchResult = ko.observableArray();

        self.sketchFileButton.fileupload({
            maxNumberOfFiles: 1,
            headers: OctoPrint.getRequestHeaders(),
            done: function(e, data) {
                new PNotify({
                    title: gettext("Sketch upload successful"),
                    text: data.result.ino,
                    type: "success"
                });
            },
            error: function(jqXHR, status, error) {
                new PNotify({
                    title: gettext("Sketch upload failed"),
                    text: jqXHR.responseJSON.error,
                    type: "error"
                });
            }
        });
        self.searchCore = function(form) {
            //show loading
            $.ajax({
                type: "GET",
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
                    text: jqXHR.responseJSON.error,
                    type: "error"
                });
            }).always(function() {
                //hide loading
            });
        };
        self.installCore = function() {
            //show loading
            $.ajax({
                type: "POST",
                url: "/plugin/marlin_flasher/cores/install",
                data: {
                    core: this.ID
                }
            }).done(function(data) {
                self.loadBoardSelectOptions();
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
                //hide loading
            });
        };
        self.uninstallCore = function() {
            //show loading
            $.ajax({
                type: "POST",
                url: "/plugin/marlin_flasher/cores/uninstall",
                data: {
                    core: this.ID
                }
            }).done(function(data) {
                self.loadBoardSelectOptions();
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
                //hide loading
            });
        };
        self.searchLib = function(form) {
            //self.libsTable.bootstrapTable("showLoading");
            $.ajax({
                type: "GET",
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
                //self.libsTable.bootstrapTable("hideLoading");
            });
        };
        self.installLib = function() {
            //self.libsTable.bootstrapTable("showLoading");
            $.ajax({
                type: "POST",
                url: "/plugin/marlin_flasher/libs/install",
                data: {
                    lib: this.Name
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
                //self.libsTable.bootstrapTable("hideLoading");
            });
        };
        self.uninstallLib =  function() {
            //self.libsTable.bootstrapTable("showLoading");
            $.ajax({
                type: "POST",
                url: "/plugin/marlin_flasher/libs/uninstall",
                data: {
                    lib: this.Name
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
                //self.libsTable.bootstrapTable("hideLoading");
            });
        };
        self.loadBoardSelectOptions = function() {
            self.fqbn.empty();
            self.fqbn.append($("<option>", {
                disabled: true,
                selected: true,
                value: "",
                text: gettext("Please select one")
            }));
            self.flashOptionContainer.empty();
            $.ajax({
                type: "GET",
                url: "/plugin/marlin_flasher/board/listall",
            }).done(function (data) {
                if(data.boards) {
                    data.boards.forEach(function(board) {
                        self.fqbn.append($("<option>", {
                            text: board.name,
                            value: board.fqbn
                        }));
                    });
                }
            }).fail(function(jqXHR, status, error) {
                new PNotify({
                    title: gettext("Board list fetch failed"),
                    text: jqXHR.responseJSON.error,
                    type: "error"
                });
            });
        };
        self.loadBoardSelectOptions();
        self.flashForm.submit(function(event) {
            self.flashButton.button("loading");
            $.ajax({
                type: "POST",
                url: "/plugin/marlin_flasher/flash",
                data: self.flashForm.serialize()
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
            }).always(function() {
                self.flashButton.button("reset");
            });
            event.preventDefault();
        });
        self.fqbn.change(function() {
            self.flashOptionContainer.empty();
            $.ajax({
                type: "GET",
                url: "/plugin/marlin_flasher/board/details",
                data: {
                    fqbn: self.fqbn.val()
                }
            }).done(function (data) {
                if(data) {
                    data.ConfigOptions.forEach(function(o) {
                        var controlGroup = $("<div>", {
                            class: "control-group"
                        });
                        controlGroup.append($("<label>", {
                            class: "control-label",
                            for: "flash-option-" + o.Option,
                            text: o.OptionLabel
                        }));
                        var controls = $("<div>", {
                            class: "controls"
                        });
                        var select = $("<select>", {
                            id: "flash-option-" + o.Option,
                            name: o.Option,
                            required: true
                        });
                        o.Values.forEach(function(v) {
                            var option = $("<option>", {
                                value: v.Value,
                                text: v.ValueLabel
                            });
                            if(v.hasOwnProperty("Selected") && v.Selected) {
                                option.prop("selected", true)
                            }
                            select.append(option);
                        });
                        controls.append(select);
                        controlGroup.append(controls);
                        self.flashOptionContainer.append(controlGroup);
                    });
                }
            }).fail(function(jqXHR, status, error) {
                new PNotify({
                    title: gettext("Board option fetch failed"),
                    text: jqXHR.responseJSON.error,
                    type: "error"
                });
            });
        });
    }

    OCTOPRINT_VIEWMODELS.push({
        construct: MarlinFlasherViewModel,
        dependencies: [
            "settingsViewModel"
        ],
        elements: [
            "#settings_plugin_marlin_flasher",
            "#wizard_plugin_marlin_flasher",
            "#tab_plugin_marlin_flasher"
        ]
    });
});
