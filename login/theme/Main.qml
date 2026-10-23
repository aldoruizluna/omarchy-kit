import QtQuick 2.0
import SddmComponents 2.0

// Omarchy Kit login screen: Omarchy's own look (the same logo, lock and entry pictures, copied from its theme when this one is installed)
// plus a row that lists every account, so you choose who is signing in. Left and Right (or Tab), or a click, change the account.
// It reads the accounts from SDDM, so no name is written in this file.
Rectangle {
  id: root
  width: 640
  height: 480
  color: "#1a1b26"

  readonly property color textOn: "#c0caf5"
  readonly property color textOff: "#565f89"
  readonly property int roleName: 257        // Qt.UserRole + 1: the account name (what SDDM logs in)
  readonly property int roleRealName: 258    // Qt.UserRole + 2: the full name

  property int userIndex: userModel.count > 0 ? Math.max(0, Math.min(userModel.lastIndex, userModel.count - 1)) : 0
  property string currentUser: userModel.count > 0 ? userModel.data(userModel.index(userIndex, 0), roleName) : userModel.lastUser
  property bool loginFailed: false
  property int sessionIndex: {
    for (var i = 0; i < sessionModel.rowCount(); i++) {
      var name = (sessionModel.data(sessionModel.index(i, 0), Qt.DisplayRole) || "").toString()
      if (name.indexOf("uwsm") !== -1)
        return i
    }
    return sessionModel.lastIndex
  }

  function selectUser(i) {
    if (userModel.count < 1) return
    userIndex = (i + userModel.count) % userModel.count
    loginFailed = false
    password.text = ""
    password.forceActiveFocus()
  }

  Connections {
    target: sddm
    function onLoginFailed() {
      root.loginFailed = true
      password.text = ""
      password.focus = true
    }
    function onLoginSucceeded() {
      root.loginFailed = false
    }
  }

  Column {
    anchors.centerIn: parent
    spacing: 34

    Image {
      id: logo
      source: "logo.png"
      width: Math.min(sourceSize.width, root.width * 0.8)
      height: sourceSize.width > 0 ? Math.round(width * sourceSize.height / sourceSize.width) : 0
      fillMode: Image.PreserveAspectFit
      anchors.horizontalCenter: parent.horizontalCenter
    }

    // who is signing in: every account, the chosen one bright
    Row {
      id: accounts
      anchors.horizontalCenter: parent.horizontalCenter
      spacing: 36

      Repeater {
        model: userModel

        Text {
          property bool chosen: index === root.userIndex
          text: (model.realName || model.name || "").toString()
          color: chosen ? root.textOn : root.textOff
          font.family: "JetBrainsMono Nerd Font"
          font.pixelSize: 24
          font.bold: chosen
          anchors.verticalCenter: parent.verticalCenter

          MouseArea {
            anchors.fill: parent
            anchors.margins: -10
            cursorShape: Qt.PointingHandCursor
            onClicked: root.selectUser(index)
          }
        }
      }
    }

    Row {
      anchors.horizontalCenter: parent.horizontalCenter
      spacing: 15

      Image {
        source: root.loginFailed ? "lock-failed.png" : "lock.png"
        width: 34
        height: 38
        fillMode: Image.PreserveAspectFit
        anchors.verticalCenter: parent.verticalCenter
      }

      Item {
        width: entry.width
        height: entry.height

        Image {
          id: entry
          source: root.loginFailed ? "entry-failed.png" : "entry.png"
          anchors.centerIn: parent
        }

        Row {
          anchors.left: parent.left
          anchors.leftMargin: 20
          anchors.verticalCenter: parent.verticalCenter
          spacing: 5

          Repeater {
            model: Math.min(password.text.length, 21)

            Image {
              source: "bullet.png"
              width: 7
              height: 7
            }
          }
        }

        TextInput {
          id: password
          anchors.fill: parent
          anchors.leftMargin: 20
          anchors.rightMargin: 20
          verticalAlignment: TextInput.AlignVCenter
          echoMode: TextInput.Password
          font.family: "JetBrainsMono Nerd Font"
          font.pixelSize: 24
          font.letterSpacing: 5
          passwordCharacter: "•"
          color: "transparent"
          selectionColor: "transparent"
          selectedTextColor: "transparent"
          cursorDelegate: Item {}
          focus: true

          onTextChanged: root.loginFailed = false

          Keys.onPressed: {
            if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter) {
              sddm.login(root.currentUser, password.text, root.sessionIndex)
              event.accepted = true
            } else if (event.key === Qt.Key_Left || event.key === Qt.Key_Up) {
              root.selectUser(root.userIndex - 1)
              event.accepted = true
            } else if (event.key === Qt.Key_Right || event.key === Qt.Key_Down || event.key === Qt.Key_Tab) {
              root.selectUser(root.userIndex + 1)
              event.accepted = true
            } else if (event.key === Qt.Key_Backtab) {
              root.selectUser(root.userIndex - 1)
              event.accepted = true
            }
          }
        }
      }
    }

    Text {
      anchors.horizontalCenter: parent.horizontalCenter
      visible: userModel.count > 1
      text: "← →"
      color: root.textOff
      font.family: "JetBrainsMono Nerd Font"
      font.pixelSize: 18
    }
  }

  Component.onCompleted: password.forceActiveFocus()
}
