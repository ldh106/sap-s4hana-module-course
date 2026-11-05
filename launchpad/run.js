/* app.html?app=... : 셸 막대 아래에 앱 Component 하나를 띄웁니다 (Fiori 런치패드가 앱을 여는 방식과 비슷) */
sap.ui.define([
    "sap/f/ShellBar", "sap/ui/core/ComponentContainer", "gaon/launchpad/apps"
], (ShellBar, ComponentContainer, APPS) => {
    "use strict";

    const sId = new URLSearchParams(window.location.search).get("app");
    const oApp = APPS.flatMap((g) => g.items).find((a) => a.id === sId);
    const sTitle = oApp ? `${oApp.title} ${oApp.subtitle}` : "앱을 찾을 수 없습니다";
    document.title = sTitle;

    new ShellBar({
        title: sTitle,
        showNavButton: true,
        navButtonPressed: () => { window.location.href = "index.html"; }
    }).placeAt("shell");

    if (oApp) {
        new ComponentContainer({
            name: oApp.component,
            async: true,
            manifest: true,
            height: "100%",
            settings: { id: oApp.component }
        }).placeAt("app");
    }
});
