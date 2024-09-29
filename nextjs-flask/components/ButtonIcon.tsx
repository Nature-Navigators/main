import { ChevronRightIcon } from "@radix-ui/react-icons";

import { Button } from "./ui/Button";

export function ButtonIcon() {
  return (
    <Button variant="outline" size="icon">
      <ChevronRightIcon className="h-4 w-4" />
    </Button>
  );
}
