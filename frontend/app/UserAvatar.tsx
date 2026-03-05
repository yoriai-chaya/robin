"use client";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";

const UserAvatar = () => {
  return (
    <>
      {/* column-A */}
      <div>
        <Avatar className="bg-blue-100">
          <AvatarImage src="/you.png" />
          <AvatarFallback>Yo</AvatarFallback>
        </Avatar>
      </div>
      {/* column-B */}
      <span className="col-span-1 text-app-avatar">You</span>
    </>
  );
};

export default UserAvatar;
