/* 런치패드 첫 화면: 셸 막대 + 그룹별 타일 */
sap.ui.define([
    "sap/m/App", "sap/m/Page", "sap/m/Title", "sap/m/Text", "sap/m/MessageStrip", "sap/m/FlexBox", "sap/m/VBox",
    "sap/m/GenericTile", "sap/m/TileContent", "sap/m/NumericContent", "sap/m/ImageContent", "sap/f/ShellBar",
    "gaon/launchpad/apps"
], (App, Page, Title, Text, MessageStrip, FlexBox, VBox, GenericTile, TileContent, NumericContent, ImageContent, ShellBar, APPS) => {
    "use strict";

    fetch("tiles.json").then((r) => r.json()).catch(() => ({})).then((oCount) => {
        const aContent = [
            new MessageStrip({
                type: "Information", showIcon: true,
                text: "교육용 런치패드입니다. 데이터는 가상 회사 가온전자의 석 달치입니다. 각 앱 오른쪽 아래 '구성 보기'를 켜고 화면을 누르면 어떤 컨트롤과 데이터로 만들어졌는지 보입니다."
            }).addStyleClass("sapUiSmallMarginBottom")
        ];
        APPS.forEach((g) => {
            aContent.push(new Title({ text: g.group, level: "H3" }).addStyleClass("sapUiSmallMarginTop sapUiTinyMarginBottom"));
            aContent.push(new FlexBox({
                wrap: "Wrap",
                items: g.items.map((a) => new GenericTile({
                    header: a.title,
                    subheader: a.subtitle,
                    press: () => { window.location.href = a.href || ("app.html?app=" + a.id); },
                    tileContent: [new TileContent({
                        unit: a.count ? a.unit : "",
                        footer: a.href ? "코스 페이지로 이동" : (a.footer || ""),
                        content: a.count
                            ? new NumericContent({ value: oCount[a.count] ? Number(oCount[a.count]).toLocaleString("ko-KR") : "", icon: a.icon, withMargin: false, formatterValue: false })
                            : new ImageContent({ src: a.icon })
                    })]
                }).addStyleClass("sapUiTinyMarginEnd sapUiTinyMarginBottom"))
            }));
        });
        new App({
            pages: [new Page({
                showHeader: false,
                content: [
                    new ShellBar({ title: (oCount.company || "가온전자") + " · Fiori 런치패드 (교육용)" }),
                    new VBox({ items: aContent }).addStyleClass("sapUiMediumMargin")
                ]
            })]
        }).placeAt("content");
    });
});
