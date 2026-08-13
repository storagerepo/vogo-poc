import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from "react";

type Ctx = {
  open: boolean;
  vehicle: string;
  openModal: (vehicle?: string) => void;
  closeModal: () => void;
};

const TestDriveContext = createContext<Ctx | null>(null);

export function TestDriveProvider({ children }: { children: ReactNode }) {
  const [open, setOpen] = useState(false);
  const [vehicle, setVehicle] = useState("");

  const openModal = useCallback((v?: string) => {
    setVehicle(v ?? "");
    setOpen(true);
  }, []);
  const closeModal = useCallback(() => setOpen(false), []);

  const value = useMemo(
    () => ({ open, vehicle, openModal, closeModal }),
    [open, vehicle, openModal, closeModal],
  );

  return <TestDriveContext.Provider value={value}>{children}</TestDriveContext.Provider>;
}

export function useTestDrive() {
  const ctx = useContext(TestDriveContext);
  if (!ctx) throw new Error("useTestDrive must be used inside TestDriveProvider");
  return ctx;
}
