from register import register_face 
from train import train_model, load_label_dict  
from recognize_with_gsheets import recognize_face  
def main():
    label_dict = None
    while True:
        print("\n=== Menu Face Recognition ===")
        print("1. Registrasi (dengan training otomatis)")
        print("2. Recognition (upload ke Google Sheets)")
        print("3. Keluar")
        choice = input("Pilih menu: ").strip()

        if choice == '1':
            register_face()
            print("Registrasi selesai. Menjalankan training otomatis...")
            label_dict = train_model()
            if label_dict:
                print("Training berhasil. Model siap digunakan.")
            else:
                print("Training gagal. Periksa dataset.")
        elif choice == '2':
            if label_dict is None:
                label_dict = load_label_dict()
                if label_dict is None:
                    print("Silakan lakukan registrasi terlebih dahulu untuk training otomatis.")
                    continue
            recognize_face() 
        elif choice == '3':
            print("Keluar program.")
            break
        else:
            print("Pilihan tidak valid.")

if __name__ == "__main__":
    main()
