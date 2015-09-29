(function($) {

$.fn.tokenInput = function (url, of_chest, options) {
    var settings = $.extend({
        url: url,
        hintText: "Type in a search term",
        noResultsText: "No results",
        searchingText: "Searching...",
        searchDelay: 300
    }, options);

    settings.classes = $.extend({
        tokenList: "token-input-list",
        token: "token-input-token",
        tokenDelete: "token-input-delete-token",
        selectedToken: "token-input-selected-token",
        highlightedToken: "token-input-highlighted-token",
        dropdown: "token-input-dropdown",
        dropdownItem: "token-input-dropdown-item",
        dropdownItem2: "token-input-dropdown-item2",
        selectedDropdownItem: "token-input-selected-dropdown-item",
        inputToken: "token-input-input-token"
    }, options.classes);

    return this.each(function () {
        var list = new $.TokenList(this, settings, of_chest);
    });
};

$.TokenList = function (input, settings, chests) {
    //
    // Variables
    //

    // Input box position "enum"
    var POSITION = {
        BEFORE: 0,
        AFTER: 1,
        END: 2
    };

    // Keys "enum"
    var KEY = {
        BACKSPACE: 8,
        RETURN: 13,
        LEFT: 37,
        UP: 38,
        RIGHT: 39,
        DOWN: 40
    };

    // Save the tokens
    var saved_tokens = [];

    // Basic cache to save on db hits
    var cache = new $.TokenList.Cache();

    // Keep track of the timeout
    var timeout;

    // Create a new text input an attach keyup events
    var input_box = $("<input type=\"text\">")
        .css({
            outline: "none"
        })
        .focus(function () {
            show_dropdown_hint();
        })
        .blur(function () {
            if(!selected_dropdown_item) {
                hide_dropdown();
            }
        })
        .keydown(function (event) {
            var previous_token;
            var next_token;

            switch(event.keyCode) {
                case KEY.LEFT:
                case KEY.RIGHT:
                case KEY.UP:
                case KEY.DOWN:
                    if($(this).val()) {
                        var dropdown_item = null;

                        if(event.keyCode == KEY.DOWN || event.keyCode == KEY.RIGHT) {
                            dropdown_item = $(selected_dropdown_item).next();
                        } else {
                            dropdown_item = $(selected_dropdown_item).prev();
                        }

                        if(dropdown_item.length) {
                            select_dropdown_item(dropdown_item);
                        }
                        return false;
                    }
                    break;

                case KEY.BACKSPACE:
                    previous_token = input_token.prev();

                    if(!$(this).val().length) {
                        if(selected_token) {
                            delete_token($(selected_token));
                        } else if(previous_token.length) {
                            select_token($(previous_token.get(0)));
                        }

                        return false;
                    } else if($(this).val().length == 1) {
                        hide_dropdown();
                    } else {
                        show_dropdown_searching();
                        do_search(1);
                    }
                    break;

                case KEY.RETURN:
                    if(selected_dropdown_item) {
                        add_token($(selected_dropdown_item));
                    }
                    return false;
                    break;

                default:
                    if(is_printable_character(event.keyCode)) {
                        show_dropdown_searching();
                        clearTimeout(timeout);
                        timeout = setTimeout(do_search, settings.searchDelay);
                    }

                    break;
            }
        });

    // Keep a reference to the original input box
    var hidden_input = $(input)
                           .hide()
                           .focus(function () {
                               input_box.focus();
                           })
                           .blur(function () {
                               input_box.blur();
                           })
                           .val("");

    // Keep a reference to the selected token and dropdown item
    var selected_token = null;
    var selected_dropdown_item = null;

    // The list to store the token items in
    var token_list = $("<ul />")
        .addClass(settings.classes.tokenList)
        .insertAfter(hidden_input)
        .click(function (event) {
            var li = get_element_from_event(event, "li");
            if(li && li.get(0) != input_token.get(0)) {
                toggle_select_token(li);
                return false;
            } else {
                input_box.focus();

                if(selected_token) {
                    deselect_token($(selected_token), POSITION.END);
                }
            }
        })
        .mouseover(function (event) {
            var li = get_element_from_event(event, "li");
            if(li && selected_token !== this) {
                li.addClass(settings.classes.highlightedToken);
            }
        })
        .mouseout(function (event) {
            var li = get_element_from_event(event, "li");
            if(li && selected_token !== this) {
                li.removeClass(settings.classes.highlightedToken);
            }
        })
        .mousedown(function (event) {
            // Stop user selecting text on tokens
            var li = get_element_from_event(event, "li");
            if(li){
                return false;
            }
        });


    // The list to store the dropdown items in
    var dropdown = $("<div>")
        .addClass(settings.classes.dropdown)
        .insertAfter(token_list)
        .hide();

    // The token holding the input box
    var input_token = $("<li />")
        .addClass(settings.classes.inputToken)
        .appendTo(token_list)
        .append(input_box);

    //
    // Functions
    //

    function is_printable_character(keycode) {
        if((keycode >= 48 && keycode <= 90) ||      // 0-1a-z
           (keycode >= 96 && keycode <= 111) ||     // numpad 0-9 + - / * .
           (keycode >= 186 && keycode <= 192) ||    // ; = , - . / ^
           (keycode >= 219 && keycode <= 222)       // ( \ ) '
          ) {
              return true;
          } else {
              return false;
          }
    }

    // Get an element of a particular type from an event (click/mouseover etc)
    function get_element_from_event (event, element_type) {
        var target = $(event.target);
        var element = null;

        if(target.is(element_type)) {
            element = target;
        } else if(target.parent(element_type).length) {
            element = target.parent(element_type+":first");
        }

        return element;
    }

    function of_chest (li_data) {
        var this_token = $("<li><p>"+ li_data.name +"</p> </li>")
            .addClass(settings.classes.token)
            .insertBefore(input_token);

        $("<span>x</span>")
            .addClass(settings.classes.tokenDelete)
            .appendTo(this_token)
            .click(function () {
                delete_token($(this).parent());
                return false;
            });

        $.data(this_token.get(0), "tokeninput", {"id": li_data.id, "name": li_data.name});
        // Save this token id
        var id_string = li_data.id + ","
        hidden_input.val(hidden_input.val() + id_string);
    }
    // Add a token to the token list
    function add_token (item) {
        var li_data = $.data(item.get(0), "tokeninput");
        var dup = false;
        var tokens = input_token.parent().children();
        for (var i = 0; i < tokens.size() - 1; i++) {
            if ($.data(tokens[i], 'tokeninput').id == li_data.id) {
                dup = true;
            }
        }
        if (!dup) {
            of_chest(li_data);
        }
        // Clear input box and make sure it keeps focus
        input_box
            .val("")
            .focus();

        // Don't show the help dropdown, they've got the idea
        hide_dropdown();

    }

    // Select a token in the token list
    function select_token (token) {
        token.addClass(settings.classes.selectedToken);
        selected_token = token.get(0);

        // Hide input box
        input_box.val("");

        // Hide dropdown if it is visible (eg if we clicked to select token)
        hide_dropdown();
    }

    // Deselect a token in the token list
    function deselect_token (token, position) {
        token.removeClass(settings.classes.selectedToken);
        selected_token = null;

        if(position == POSITION.BEFORE) {
            input_token.insertBefore(token);
        } else if(position == POSITION.AFTER) {
            input_token.insertAfter(token);
        } else {
            input_token.appendTo(token_list);
        }

        // Show the input box and give it focus again
        input_box.focus();
    }

    // Toggle selection of a token in the token list
    function toggle_select_token (token) {
        if(selected_token == token.get(0)) {
            deselect_token(token, POSITION.END);
        } else {
            if(selected_token) {
                deselect_token($(selected_token), POSITION.END);
            }
            select_token(token);
        }
    }

    // Delete a token from the token list
    function delete_token (token) {
        // Remove the id from the saved list
        var token_data = $.data(token.get(0), "tokeninput");
        //saved_tokens.splice($.inArray(saved_tokens, token_data.id), 1);

        // Delete the token
        token.remove();
        selected_token = null;

        // Show the input box and give it focus again
        input_box.focus();

        // Delete this token's id from hidden input
        var str = hidden_input.val()
        var start = str.indexOf(token_data.id+",");
        var end = str.indexOf(",", start) + 1;

        if(end >= str.length) {
            hidden_input.val(str.slice(0, start));
        } else {
            hidden_input.val(str.slice(0, start) + str.slice(end, str.length));
        }
    }

    // Hide and clear the results dropdown
    function hide_dropdown () {
        dropdown.hide().empty();
        selected_dropdown_item = null;
    }

    function show_dropdown_searching () {
        dropdown
            .html("<p>"+settings.searchingText+"</p>")
            .show();
    }

    function show_dropdown_hint () {
        dropdown
            .html("<p>"+settings.hintText+"</p>")
            .show();
    }

    function show_dropdown_dup () {
        dropdown
            .html("<p>"+settings.dupText+"</p>")
            .show();
    }

    // Highlight the query part of the search term
    function highlight_term(value, term) {
        return value.replace(new RegExp("(?![^&;]+;)(?!<[^<>]*)(" + term + ")(?![^<>]*>)(?![^&;]+;)", "gi"), "<em>$1</em>");
    }

    // Populate the results dropdown with some results
    function populate_dropdown (query, results) {
        sarin = results;
        if(results.length) {
            dropdown.empty();
            var dropdown_ul = $("<ul>")
                .appendTo(dropdown)
                .mouseover(function (event) {
                    select_dropdown_item(get_element_from_event(event, "li"));
                })
                .click(function (event) {
                    add_token(get_element_from_event(event, "li"));
                })
                .mousedown(function (event) {
                    // Stop user selecting text on tokens
                    return false;
                })
                .hide();

            for(var i in results) {
                if (results.hasOwnProperty(i)) {
                    var this_li = $("<li>"+highlight_term(results[i].name, query)+"</li>")
                                      .appendTo(dropdown_ul);

                    if(i%2) {
                        this_li.addClass(settings.classes.dropdownItem);
                    } else {
                        this_li.addClass(settings.classes.dropdownItem2);
                    }

                    if(i == 0) {
                        select_dropdown_item(this_li);
                    }

                    $.data(this_li.get(0), "tokeninput", {"id": results[i].id, "name": results[i].name});
                }
            }

            dropdown.show();
            dropdown_ul.slideDown("fast");

        } else {
            dropdown
                .html("<p>"+settings.noResultsText+"</p>")
                .show();
        }
    }

    // Highlight an item in the results dropdown
    function select_dropdown_item (item) {
        if(item) {
            if(selected_dropdown_item) {
                deselect_dropdown_item($(selected_dropdown_item));
            }

            item.addClass(settings.classes.selectedDropdownItem);
            selected_dropdown_item = item.get(0);
        }
    }

    // Remove highlighting from an item in the results dropdown
    function deselect_dropdown_item (item) {
        item.removeClass(settings.classes.selectedDropdownItem);
        selected_dropdown_item = null;
    }

    // Do a search
    function do_search(trim_last_char) {
        var query = input_box.val().toLowerCase();

        if(trim_last_char == 1) {
            query = query.substring(0, query.length-1);
        }

        if(query && query.length) {
            if(selected_token) {
                deselect_token($(selected_token), POSITION.AFTER);
            }

            var cached_results = cache.get(query);
            if(cached_results) {
                populate_dropdown(query, cached_results);
            } else {
                $.get(settings.url, {"q": query }, function (results) {
                    cache.add(query, results);
                    populate_dropdown(query, results);
                }, "json");
            }
        }
    }
    for (oc in chests) {
        of_chest(chests[oc]);
    }
};

// Really basic cache for the results
$.TokenList.Cache = function (options) {
    var settings = $.extend({
        max_size: 10
    }, options);

    var data = {};
    var size = 0;

    var flush = function () {
        data = {};
        size = 0;
    };

    this.add = function (query, results) {
        if(size > settings.max_size) {
            flush();
        }

        if(!data[query]) {
            size++;
        }

        data[query] = results;
    };

    this.get = function (query) {
        return data[query];
    };
};

})(jQuery);
