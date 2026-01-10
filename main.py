from register import register_face  # fungsi registrasi
from train import train_model, load_label_dict  # fungsi training
from recognize_with_gsheets import recognize_face  # recognition yg sudah include upload sheets

def main():
    label_dict = None
    while True:
        print("\n=== Menu Face Recognition ===")
        print("1. Registrasi (dengan training otomatis)")
        print("2. Recognition (upload ke Google Sheets)")
        print("3. Keluar")
        choice = input("Pilih menu: ").strip()

        if choice == '1':
            # Jalankan registrasi
            register_face()
            # Setelah registrasi selesai, jalankan training otomatis
            print("Registrasi selesai. Menjalankan training otomatis...")
            label_dict = train_model()
            if label_dict:
                print("Training berhasil. Model siap digunakan.")
            else:
                print("Training gagal. Periksa dataset.")
        elif choice == '2':
            # Load label_dict kalau belum ada
            if label_dict is None:
                label_dict = load_label_dict()
                if label_dict is None:
                    print("Silakan lakukan registrasi terlebih dahulu untuk training otomatis.")
                    continue
            recognize_face()  # langsung jalankan recognize yang upload ke Google Sheets
        elif choice == '3':
            print("Keluar program.")
            break
        else:
            print("Pilihan tidak valid.")

if __name__ == "__main__":
    main()