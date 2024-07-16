var user = {
  name: "",
  nickname: "",
  email: "",
  email_verified: "false",
  status: "",
  update: function (userInfo) {
    for (key in userInfo) {
      if (this[key] != undefined) {
        this[key] = userInfo[key];
      }
    }
  }
};

var apiURL = localStorage["apiURL"]

function inputCredentials() {
  if ((localStorage["aws-congnito-user-pool-id"] !== undefined) &&
    (localStorage["aws-congnito-app-id"] !== undefined) &&
    (localStorage["apiURL"] !== undefined)) {
    $("#cognitoUserPoolId").val(localStorage["aws-congnito-user-pool-id"]);
    $("#applicationId").val(localStorage["aws-congnito-app-id"]);
    $("#apiURL").val(localStorage["apiURL"]);
  }
  $("#credentialsModal").modal();
}

function saveCredentials() {
  let userPoolId = $("#cognitoUserPoolId").val();
  localStorage.setItem("aws-congnito-user-pool-id", userPoolId);
  let appId = $("#applicationId").val();
  localStorage.setItem("aws-congnito-app-id", appId);
  let apiURL = $("#apiURL").val();
  localStorage.setItem("apiURL", apiURL);
}

function clearCredentials() {
  localStorage.removeItem("aws-congnito-user-pool-id");
  localStorage.removeItem("aws-congnito-app-id");
  localStorage.removeItem("apiURL");
  $("#cognitoUserPoolId").val("");
  $("#applicationId").val("");
  $("#apiURL").val("");
}

function visibility(divElementId, show = false) {
  let divElement = document.getElementById(divElementId);
  if (show) {
    divElement.style.display = "block";
  }
  else {
    divElement.style.display = "none";
  }
}

function showAlertMessage(alertType, message) {
  $("#operationAlert span").remove();
  $("#operationAlert").attr('class', "alert alert-" + alertType);
  $("#operationAlert button").after('<span>' + message + '</span>');
  $("#operationAlert").fadeIn('slow');
  $("#operationAlert").show();
}

function closeAlertMessage() {
  $("#operationAlert span").remove();
  $("#operationAlert").hide();
}

function createCallback(successMessage, userName = "", email = "", confirmed = "", status = "") {
  return (err, result) => {
    if (err) {
      message = "<strong>" + err.name + "</strong>: " + err.message;
      showAlertMessage('danger', message);
    }
    else {
      user.update({
        name: userName,
        email: email,
        email_verified: confirmed,
        status: status
      });
      message = "<strong>Success</strong>: " + successMessage;
      showAlertMessage('success', message);
      userAttributes(updateTable);
    }
  };
}


function modalFormEnter() {
  let buttonText = $("#modalFormButton").text();
  let username = $("#userName").val();
  let password = $("#userPassword").val();

  let callback;
  let message;
  switch (buttonText) {
    case "Sign In":
      message = `user <i>${username}</i> signed in`;
      callback = createCallback(message, username, "", "true", "Signed In", "");
      signInUser(username, password, callback);
      break;
  }
  $("#addUserModal").modal('hide');
}


function updateModal(showName, showEmail, showPassword, showNewPassword, showConfirm, buttonText, title) {
  visibility("userNameDiv", showName);
  visibility("userEmailDiv", showEmail);
  if (showNewPassword) {
    visibility("userNewPasswordDiv", true);
    $("#passwordLabel").text("Current Password");
  }
  else {
    visibility("userNewPasswordDiv", false);
    $("#passwordLabel").text("Password");
  }
  visibility("userPasswordDiv", showPassword);
  visibility("confirmationCode", showConfirm);
  $("#modalFormButton").text(buttonText);
  $("#addUserModalLabel").text(title);
  $("#addUserModal").modal();

}

function toggleShowPassword(checkBoxId, inputId) {
  if ($("#" + checkBoxId).is(":checked")) {
    $("#" + inputId).prop("type", "text");
  }
  else {
    $("#" + inputId).prop("type", "password");
  }
}


function actionSignInUser() {
  updateModal(true, false, true, false, false, "Sign In", "Authenticate user");
}

function actionSignOutUser() {
  let message = `user <i>${user.name}</i> signed out`
  let callback = createCallback(message, user.name,
    user.email, user.email_verified, "Signed Out");
  signOutUser(callback);
  visibility("userNameCell", false);
  visibility("userNickNameCell", false);
  visibility("userEmailCell", false);
  visibility("bedrock", false);
  visibility("bedrock-cost", false);
  visibility("costTable", false);
  visibility("bedrock-cost-calculate", false);
  window.location.reload()
}

function updateTable(userInfo) {
  user.update(userInfo);
  $("#userNameCell").html(user.name);
  $('#userNickNameCell').html(user.nickname);
  $("#userEmailCell").html(user.email);
  if (user.email === "admin@amazon.com") {
    visibility("bedrock", false);
    visibility("bedrock-cost", true);
    visibility("bedrock-cost-calculate", true);
  }
  else {
    visibility("bedrock", true);
  }
}

function invokeModel() {
  visibility("loading", true);
  const model_id = document.getElementById("model-id").value;
  console.log(model_id);
  const bedrock_text = document.getElementById('bedrock-text').value;
  var invokeURL = `${apiURL}/invoke_model?model_id=${model_id}`
  var myHeaders = new Headers();
  myHeaders.append("Access-Control-Allow-Origin", '*')
  myHeaders.append("Auth", localStorage['idtoken']);
  if (model_id === "anthropic.claude-3-sonnet-20240229-v1:0") {
    /*var process_input = {
      "anthropic_version": "bedrock-2023-05-31",
      "max_tokens":1000,
      "messages": [{"role": "user", "content":{"type":"text","text": bedrock_text}}]
    }*/
    var raw = JSON.stringify({ "inputs": bedrock_text });
  }
  else {
    var raw = JSON.stringify({ "inputs": bedrock_text, "parameters": { "maxTokenCount": 4096, "temperature": 0.8 } });
  }
  var requestOptions = {
    method: 'POST',
    headers: myHeaders,
    body: raw,
    timeout: 5000,
  };
  console.log(invokeURL)
  fetch(invokeURL, requestOptions)
    .then(response => {
      return response.json()
    }).then(result => {
      visibility("loading", false);
      var targetDiv = $('#bedrock-result');
      targetDiv.html(result[0]['generated_text']);
    }).catch(error => console.log('error', error));

}

function ddb_cost_retrieval() {
  var trackURL = `${apiURL}/ddb_cost_retrieval`
  var myHeaders = new Headers();
  myHeaders.append("Access-Control-Allow-Origin", '*')
  myHeaders.append("Auth", localStorage['idtoken']);
  var requestOptions = {
    method: 'POST',
    headers: myHeaders,
    timeout: 5000,
  };
  fetch(trackURL, requestOptions)
    .then(response => {
      return response.json()
    }).then(result => {
      console.log(result['body'])
      console.log(result['body'].length)

      let contentstr = '<tbody>';
      for (let j = 0; j < result['body'].length; j++) {
        console.log(result['body'][j])
        let rc = result['body'][j];
        contentstr = contentstr +
          `<tr>
						<td>${rc['name']}</td>                     
						<td>${rc['model_id']}</td>
						<td>${rc['input_tokens']}</td>
						<td>${rc['output_tokens']}</td>
						<td>${rc['input_cost']}</td>
						<td>${rc['output_cost']}</td>
						<td>${rc['date']}</td>
					</tr>`;
      }
      contentstr = contentstr + '</tbody>';
      document.getElementById("cost-detail").innerHTML = contentstr;

    }).catch(error => console.log('error', error));
  visibility("costTable", true);

}

function cost_track_manual() {
  visibility("loading", true);
  var trackURL = `${apiURL}/cost_track_manual`
  var myHeaders = new Headers();
  myHeaders.append("Access-Control-Allow-Origin", '*')
  myHeaders.append("Auth", localStorage['idtoken']);
  var requestOptions = {
    method: 'POST',
    headers: myHeaders,
    timeout: 5000,
  };
  fetch(trackURL, requestOptions)
    .then(response => {
      return response.json()
    }).then(result => {
      visibility("loading", false);
      alert(result['body'])
    }).catch(error => console.log('error', error));

}
