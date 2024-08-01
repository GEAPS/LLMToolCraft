// app.js

const supportedCommands = ["\\clipboard+"];
let clipboardQueue = [];
let highLevelView = true;
let craftToolHighLevelView = true;

var socket = io();

$(document).ready(function () {
  let accumulatedResponse = '';

  // Existing prompt-form submission logic
  $("#prompt-form").on("submit", function (event) {
    event.preventDefault();
    if (highLevelView) {
      $("#switch-view-btn").click();
    }

    highLevelView = false;
    const prompt = $("#prompt").html();
    const purified_prompt = reverseTransformation(prompt);
    console.log(purified_prompt);

    $.post("/generate", { prompt: purified_prompt }, function (data) {
      if (data.status === 'streaming') {
        $('#status').text('Generating response...');
        $('#response').html('<pre></pre>');
        accumulatedResponse = ''; 
      }
    }).fail(function (error) {
      console.error("Error:", error);
    });
  });


  // Existing socket event listeners
  socket.on('response_chunk', function (data) {
    console.log("Received chunk:", data.chunk);
    accumulatedResponse += data.chunk;
    renderMarkdown(accumulatedResponse);
  });

  socket.on('response_complete', function () {
    console.log('Response complete');
    $('#status').text('');
  });

  $("#craft-tools-form").on("submit", function (event) {
    event.preventDefault();
    if (craftToolHighLevelView) {
      $("#craft-switch-view-btn").click();
    }
  
    craftToolHighLevelView = false;
    const requirement = $("#requirement").html();
    const purified_requirement = reverseTransformation(requirement);
    console.log("Submitting requirement:", purified_requirement);
  
    $.ajax({
      url: "/craft/craft-tools",
      type: "POST",
      contentType: "application/json",
      data: JSON.stringify({ prompt: purified_requirement }),
      success: function (data) {
        console.log("Initial response:", data);
        $('#craft-state').text(data.state); // Changed from data.state to data.status
        $('#craft-response').html('<pre>' + data.response + '</pre>');
      },
      error: function (error) {
        console.error("Error:", error);
        $('#craft-response').text("Error occurred while processing the request.");
      }
    });
  });
  
  socket.on('tool_response', function(data) {
    console.log("Received tool response:", data);
    const markdownHtml = marked.parse(data.response);
    $('#craft-response').html(markdownHtml);
    $('#craft-state').text(data.state);
  });


// function renderMarkdown(responseText) {
//   const markdownHtml = marked.parse(responseText);
//   $('#response').html(markdownHtml);
// }

  // Input event handlers for both forms
  $('#prompt, #requirement').on('keypress', function (event) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      $(this).closest('form').submit();
    }
  });

  // Clipboard queue clear button
  $("#clear-queue-btn").on("click", function () {
    $.post("/clear_queue", function (data) {
      clipboardQueue = [];
      updateClipboardQueue();
    }).fail(function (error) {
      console.error("Error:", error);
    });
  });

  // Socket event for clipboard update
  socket.on('update_clipboard', function (data) {
    clipboardQueue = data;
    updateClipboardQueue();
  });

  // Input event for command suggestions
  $('#prompt, #requirement').on('input', function (event) {
    const preCursorText = getTextUpToCursor(event.target);
    const matchCommand = preCursorText.match(/\\(\w*)$/);
    const matchClipboard = preCursorText.match(/\\clipboard\+(\d+)$/);
    console.log(matchCommand);
    
    if (matchCommand) {
      showCommandSuggestions(matchCommand[1], $(this).attr('id'));
      console.log("showcommand");
    } else if (matchClipboard) {
      const id = parseInt(matchClipboard[1], 10);
      showClipboardSuggestions(id, $(this).attr('id'));
      console.log("showclippboard");
    } else {
      hideSuggestions($(this).attr('id'));
    }
  });

  // Keyboard navigation for suggestions
  $('#prompt, #requirement').on('keydown', function(event) {
    const inputId = $(this).attr('id');
    const suggestionsContainer = $(`#${inputId}-autocomplete-container`);
    const suggestions = suggestionsContainer.find(".autocomplete-suggestion");
  
    console.log(`Keydown event on ${inputId}. Suggestions container:`, suggestionsContainer);
    console.log(`Number of suggestions:`, suggestions.length);
  
    if (suggestions.length > 0) {
      if (event.key === "ArrowDown") {
        event.preventDefault();
        activeSuggestionIndex = (activeSuggestionIndex + 1) % suggestions.length;
        updateActiveSuggestion(suggestions);
      } else if (event.key === "ArrowUp") {
        event.preventDefault();
        activeSuggestionIndex = (activeSuggestionIndex - 1 + suggestions.length) % suggestions.length;
        updateActiveSuggestion(suggestions);
      } else if (event.key === "Enter") {
        event.preventDefault();
        if (activeSuggestionIndex >= 0 && activeSuggestionIndex < suggestions.length) {
          $(suggestions[activeSuggestionIndex]).click();
        }
      }
    }
  
    if (event.key === 'ArrowRight') {
      const selection = window.getSelection();
      if (selection.rangeCount > 0) {
        const range = selection.getRangeAt(0);
        if (range.startContainer === range.endContainer && range.endOffset === range.endContainer.length) {
          ensureEditableSpace($(this));
          range.collapse(false);
          selection.removeAllRanges();
          selection.addRange(range);
        }
      }
    }
  });

  // View switch buttons
  $("#switch-view-btn").on("click", function () {
    highLevelView = !highLevelView;
    transformPromptContent("#prompt");
    updateButtonText($(this), highLevelView);
  });

  $("#craft-switch-view-btn").on("click", function () {
    craftToolHighLevelView = !craftToolHighLevelView;
    transformPromptContent("#requirement");
    updateButtonText($(this), craftToolHighLevelView);
  });

  // Clear history buttons
  $('#clear-history-btn').on('click', function () {
    $.post('/clear_history', function (response) {
      if (response.status === 'success') {
        $('#status').text('History cleared. A new session has started.');
        $('#response').empty();
      } else {
        $('#status').text('Failed to clear history.');
      }
    });
  });

  // Clear history button for the craft tools tab
  $('#craft-clear-history-btn').on('click', function () {
    $.post('/craft/clear_craft_history', function (response) {
      if (response.status === 'success') {
        $('#craft-state').text('Craft history cleared. A new session has started.');
        $('#craft-response').empty();
      } else {
        $('#craft-status').text('Failed to clear craft history.');
      }
    });
  });

});

// Existing helper functions (updateClipboardQueue, getTextUpToCursor, updateActiveSuggestion, etc.)
function updateActiveSuggestion(suggestions) {
  suggestions.removeClass('active');
  if (activeSuggestionIndex >= 0 && activeSuggestionIndex < suggestions.length) {
    suggestions.eq(activeSuggestionIndex).addClass('active');
  }
  console.log(`Updated active suggestion. Index: ${activeSuggestionIndex}`);
}


function showCommandSuggestions(partialCommand, targetId) {
  if ((targetId === 'prompt' && !highLevelView) || (targetId === 'requirement' && !craftToolHighLevelView)) {
    return;
  }

  const suggestionsContainer = $(`#${targetId}-autocomplete-container`);

  if (suggestionsContainer.length === 0) {
    console.error(`Autocomplete container for ${targetId} not found`);
    return;
  }


  suggestionsContainer.empty();

  const filteredCommands = supportedCommands.filter(command => command.startsWith(`\\${partialCommand}`));
  filteredCommands.forEach(command => {
    const suggestionDiv = $("<div>", { class: "autocomplete-suggestion", text: command });
    suggestionsContainer.append(suggestionDiv);

    suggestionDiv.on("click", function () {
      const promptInput = $(`#${targetId}`);
      const selection = window.getSelection();
      const range = selection.getRangeAt(0);

      const promptText = promptInput.text();
      const cursorPosition = range.startOffset;

      const preCursorText = promptText.substring(0, cursorPosition).replace(/\\\w*$/, command);
      const postCursorText = promptText.substring(cursorPosition);
      const newText = preCursorText + postCursorText;

      promptInput.text(newText);

      const newRange = document.createRange();
      const textNode = promptInput[0].firstChild;

      if (textNode) {
        const newOffset = Math.min(preCursorText.length + command.length, textNode.textContent.length);
        newRange.setStart(textNode, newOffset);
        newRange.collapse(true);
        selection.removeAllRanges();
        selection.addRange(newRange);
      }

      hideSuggestions(targetId);
    });
  });

  activeSuggestionIndex = -1;
  suggestionsContainer.show();
}

function showClipboardSuggestions(id, targetId) {
  const suggestionsContainer = $(`#${targetId}-autocomplete-container`);
  
  // Check if the container exists
  if (suggestionsContainer.length === 0) {
    console.error(`Autocomplete container for ${targetId} not found`);
    return;
  }

  suggestionsContainer.empty();

  if (id > 0 && id <= clipboardQueue.length) {
    const suggestionDiv = $("<div>", { class: "autocomplete-suggestion", text: clipboardQueue[clipboardQueue.length - id] });
    suggestionsContainer.append(suggestionDiv);

    suggestionDiv.on("click", function () {
      hideSuggestions(targetId);
    });
  }

  activeSuggestionIndex = -1;
  suggestionsContainer.show();
}

function hideSuggestions(targetId) {
  $(`#${targetId}-autocomplete-container`).hide().empty();
  activeSuggestionIndex = -1;
}


function transformPromptContent(targetId) {
  const prompt = $(targetId).html();
  const isHighLevelView = targetId === "#prompt" ? highLevelView : craftToolHighLevelView;
  if (isHighLevelView) {
    const highLevelContent = convertToHighLevel(prompt);
    $(targetId).html(highLevelContent);
  } else {
    const lowLevelContent = convertToLowLevel(prompt);
    $(targetId).html(lowLevelContent);
  }
}

function updateButtonText(button, isHighLevelView) {
  button.text(isHighLevelView ? "Switch to Detailed View" : "Switch to Abstract View");
}

function ensureEditableSpace(element) {
  const $lastChild = element.children().last();

  if ($lastChild.length && $lastChild.hasClass("editable")) {
    const $space = $('<span>').html('&nbsp;');
    element.append($space);
    console.log("Successfully added non-breaking space");
  } else {
    console.log("No editable space", $lastChild.length, $lastChild[0].nodeType);
  }
}

function updateClipboardQueue() {
  const queueContainer = $('#clipboard-queue');
  queueContainer.empty();

  clipboardQueue.slice().reverse().forEach((text, index) => {
    const div = $('<div>', { class: 'clipboard-item' });
    const number = $('<span>', { class: 'clipboard-item-number', text: index + 1 });
    const textContent = $('<span>', { class: 'clipboard-item-text', text: text });

    div.append(number, textContent);
    queueContainer.append(div);
  });
}
// Existing functions (renderMarkdown, escapeHtml, convertToLowLevel, convertToHighLevel, reverseTransformation)

function getTextUpToCursor(node) {
  let sel = window.getSelection();
  let range = sel.getRangeAt(0);
  let preCursorRange = range.cloneRange();
  preCursorRange.selectNodeContents(node);
  preCursorRange.setEnd(range.endContainer, range.endOffset);
  return preCursorRange.toString();
}


function reverseTransformation(lowLevelContent) {
  const parser = new DOMParser();
  const doc = parser.parseFromString(lowLevelContent, 'text/html');
  const editableElements = doc.querySelectorAll('.editable');

  editableElements.forEach(element => {
    const textContent = element.firstChild.nodeValue;

    lowLevelContent = lowLevelContent.replace(element.outerHTML, textContent);
  });

  const purifiedContent = lowLevelContent.replace(/<\/?[^>]+(>|$)/g, "");

  return purifiedContent;
}

function convertToLowLevel(prompt) {
  return prompt.replace(/\\clipboard\+(\d+)/g, (_, id) => {
    const index = clipboardQueue.length - parseInt(id, 10);
    if (index >= 0 && index < clipboardQueue.length) {
      return `<div class="editable" contenteditable="true" data-id="${id}">${clipboardQueue[index]}<sup>${id}</sup></div>`;
    }
    return `\\clipboard+${id}`;
  });
}

function convertToHighLevel(prompt) {
  const parser = new DOMParser();
  const doc = parser.parseFromString(prompt, 'text/html');
  const editableElements = doc.querySelectorAll('.editable');

  editableElements.forEach(element => {
    const id = element.getAttribute('data-id');
    const text = element.innerText.replace(/\d+$/, '').trim();
    clipboardQueue[clipboardQueue.length - parseInt(id, 10)] = text;
    prompt = prompt.replace(element.outerHTML, `\\clipboard+${id}`);
  });

  updateClipboardQueue();

  return prompt;
}


function escapeHtml(text) {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function renderMarkdown(responseText) {
  const markdownHtml = marked.parse(responseText);
  $('#response').html(markdownHtml);
}