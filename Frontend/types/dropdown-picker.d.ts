declare module 'react-native-dropdown-picker' {
  export interface DropdownItem {
    label: string;
    value: any;
    [key: string]: any;
  }

  export interface DropdownPickerProps {
    open: boolean;
    value: any;
    items: DropdownItem[];
    setOpen: (open: boolean) => void;
    setValue: (value: any) => void;
    placeholder?: string;
    style?: any;
    dropDownContainerStyle?: any;
    listMode?: 'MODAL' | 'SCROLLVIEW';
    zIndex?: number;
    zIndexInverse?: number;
    [key: string]: any;
  }

  export default class DropdownPicker extends React.Component<DropdownPickerProps> {}
}
