"use client";

import React, { useTransition } from "react";
import { Button, Tooltip, notification } from "antd";
import { useLocale, useTranslations } from "next-intl";
import { setUserLocale } from "../i18n/client";

export default function LanguageSwitcher() {
  const [isPending, startTransition] = useTransition();
  const locale = useLocale();
  const t = useTranslations("common");

  const changeLocale = (nextLocale: string) => {
    if (locale === nextLocale) return;
    
    startTransition(() => {
      setUserLocale(nextLocale).then(() => {
        notification.success({
          message: nextLocale === 'tr' ? 'Dil Değiştirildi' : 'Language Changed',
          description: nextLocale === 'tr' ? 'Arayüz dili Türkçe olarak güncellendi.' : 'Interface language updated to English.',
          placement: "bottomRight"
        });
      });
    });
  };

  return (
    <div className="flex bg-[#12141d] rounded-lg p-1 border border-[#66fcf1]/20 h-9">
      <Tooltip title={t("switchToTurkish", { defaultMessage: "Türkçe" })}>
        <Button
          type="text"
          className={`h-full w-10 min-w-10 px-0 flex items-center justify-center font-mono font-bold transition-all ${
            locale === "tr"
              ? "text-[#66fcf1] bg-[#66fcf1]/10 shadow-[0_0_10px_rgba(102,252,241,0.2)]"
              : "text-gray-500 hover:text-gray-300"
          }`}
          onClick={() => changeLocale("tr")}
          loading={isPending && locale !== "tr"}
        >
          TR
        </Button>
      </Tooltip>
      <div className="w-[1px] h-full bg-[#66fcf1]/10 mx-0.5" />
      <Tooltip title={t("switchToEnglish", { defaultMessage: "English" })}>
        <Button
          type="text"
          className={`h-full w-10 min-w-10 px-0 flex items-center justify-center font-mono font-bold transition-all ${
            locale === "en"
              ? "text-[#66fcf1] bg-[#66fcf1]/10 shadow-[0_0_10px_rgba(102,252,241,0.2)]"
              : "text-gray-500 hover:text-gray-300"
          }`}
          onClick={() => changeLocale("en")}
          loading={isPending && locale !== "en"}
        >
          EN
        </Button>
      </Tooltip>
    </div>
  );
}
