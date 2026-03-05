"use client";

import * as React from "react";
import { format } from "date-fns";
import { CalendarIcon } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Calendar } from "@/components/ui/calendar";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { ja } from "date-fns/locale";
import { useState } from "react";

interface DatePickerProps {
  date: Date | undefined;
  setDate: React.Dispatch<React.SetStateAction<Date | undefined>>;
  name: string;
}
export function DatePicker({ date, setDate, name }: DatePickerProps) {
  const [open, setOpen] = useState(false);
  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button variant={"outline"} aria-label={name}>
          <CalendarIcon />
          {date ? (
            format(date, "yyyy年MM月dd日(eee)", { locale: ja })
          ) : (
            <span>日付を選択</span>
          )}
        </Button>
      </PopoverTrigger>
      <PopoverContent
        className="w-auto p-0"
        align="start"
        data-testid={`${name}-calendar`}
      >
        <Calendar
          locale={ja}
          formatters={{
            formatCaption: (d) => {
              const date = new Date(d);
              return `${date.getFullYear()}年 ${date.getMonth() + 1}月`;
            },
          }}
          mode="single"
          selected={date}
          onSelect={(selectedDate) => {
            setDate(selectedDate);
            setOpen(false);
          }}
        />
      </PopoverContent>
    </Popover>
  );
}
