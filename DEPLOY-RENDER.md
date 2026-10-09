# Đưa LinkScope lên online — GitHub + Render

**Kết quả mong muốn:** một đường link HTTPS mở trên máy tính/điện thoại, không phải chạy Python trên máy của bạn.

> Đây là gói mã nguồn đã chuẩn bị để triển khai, **chưa phải website đã được triển khai lên tài khoản Render của bạn**. Bạn cần tự đăng nhập GitHub và Render. Không gửi mật khẩu hay API Key vào chat.

## 1. Đưa đúng mã nguồn lên GitHub

1. Tải `LinkScope-Online-Render.zip`, giải nén toàn bộ.
2. Tạo một repository mới, nên chọn **Private** (dùng nội bộ).
3. Chọn **Add file → Upload files**. Kéo các FILE và thư mục bên trong gói đã giải nén vào repository.
4. Đảm bảo ngay trang chính repository nhìn thấy **`render.yaml`, `deploy_app.py`, `requirements-render.txt`, `app.py`**, cùng các thư mục `templates`, `static`, `tests`.
5. Commit changes. **Không upload nguyên file ZIP** để thay cho mã nguồn, không đặt tất cả file lồng thêm dưới thư mục `LinkScope/`.
6. Giữ `.gitignore` và `.python-version` ở gốc repo. Nếu giao diện upload bỏ qua file chấm đầu tên, dùng **Add file → Create new file** để tạo lại. `.python-version` chỉ chứa `3.13`.

Không upload `.venv`, `.env`, API Key, mật khẩu tool, file xuất Excel/CSV, file runtime hoặc log. `.gitignore` không thay việc tự kiểm tra khi bạn upload bằng trình duyệt.

## 2. Kết nối repo với Render

1. Mở **https://dashboard.render.com/**, đăng ký/đăng nhập.
2. Chọn **New → Blueprint**.
3. Kết nối GitHub, chỉ cấp quyền cho repository vừa tạo.
4. Chọn repo và nhánh chứa mã nguồn.
5. Render đọc cấu hình từ `render.yaml` ở thư mục gốc. Đặt tên Blueprint bất kỳ dễ nhớ.
6. Khi hỏi **`LINKSCOPE_PASSWORD`**, nhập mật khẩu riêng cho tool, **ít nhất 16 ký tự**, tốt nhất dùng mật khẩu ngẫu nhiên do trình quản lý mật khẩu tạo. Không dùng API Key, mật khẩu Google hoặc mật khẩu GitHub làm mật khẩu tool.
7. **`SECRET_KEY` được Render tự sinh** theo Blueprint. Không copy secret vào mã nguồn. Giữ bí mật giá trị này.
8. Kiểm tra cấu hình/chi phí rồi xác nhận tạo và triển khai.

Cấu hình đã đặt `plan: free` để thử nghiệm cá nhân; không có database hay ổ lưu trữ trả phí trong Blueprint này. Vẫn phải kiểm tra giao diện giá và hạn mức trên tài khoản Render trước khi xác nhận. Không tự nâng cấp trả phí nếu bạn chưa muốn.

## 3. Lấy đường link và sử dụng

1. Khi service báo **Live**, mở đường link `.onrender.com` mà Render cấp. Đây là đường link thật của bạn; tên chính xác có thể khác tên service nếu bị trùng.
2. Nhập mật khẩu đã đặt ở `LINKSCOPE_PASSWORD`.
3. Bên trong tool, nhập **API Key AddLiveTag** (lấy tại https://addlivetag.com/tool/api-key.php).
4. Dán danh sách link / tải Excel, CSV. Chạy thử **2–3 sản phẩm trước**.
5. Xem giá, tổng đã bán, hoa hồng và lịch sử; lọc rồi xuất Excel.

**Hai loại bí mật khác nhau:**
- Mật khẩu tool: kiểm soát ai mở được website, đặt trong Render Environment.
- API Key: quyền gọi AddLiveTag, nhập ở giao diện sau đăng nhập. Không lưu vào Git hoặc cookie.

## Cấu hình kỹ thuật có sẵn

| Mục | Giá trị |
|---|---|
| Dịch vụ | Python Web Service — không phải Static Site/GitHub Pages |
| Build Command | `pip install -r requirements-render.txt` |
| Start Command | `gunicorn --config gunicorn.conf.py deploy_app:app` |
| Health check | `/healthz` |
| Python | `.python-version`: `3.13` (Render chọn bản vá mới nhất tương ứng) |
| Số worker / instance | **1 / 1** — không tăng nếu chưa thay rate limiter bằng kho dùng chung |
| Threads | 4, chỉ 1 yêu cầu API/import/export nặng đồng thời |
| Secret bắt buộc | `LINKSCOPE_PASSWORD` ít nhất 16 ký tự; `SECRET_KEY` ít nhất 32 ký tự |

**Không đổi Start Command thành `python app.py` hoặc `gunicorn app:app`.** Hai lệnh đó là chế độ local, không nạp lớp đăng nhập của bản online. Entry point online phải là **`deploy_app:app`**.

## Bảo vệ và giới hạn của bản online

- Bắt buộc mật khẩu; thiếu cấu hình thì không khởi động (không tự mở công khai).
- Phiên có cookie Secure/HttpOnly/SameSite=Lax, thời hạn 8 giờ và gia hạn khi sử dụng. Đổi mật khẩu và redeploy sẽ vô hiệu hóa các phiên dùng mật khẩu cũ.
- Chống CSRF cho thao tác gửi dữ liệu và đăng xuất. Có header chống nhúng iframe; mở website trực tiếp, không nhúng trong website khác.
- Giới hạn sai mật khẩu: 5 lần/phút theo peer và 20 lần/phút toàn app.
- Giới hạn chung toàn tool: 5 request batch/phút, 10 request lịch sử/phút; import/export và rà soát link cũng được giới hạn.
- Một yêu cầu API/import/export nặng tại một thời điểm để hạn chế cạn RAM. Nếu hai tab cùng chạy, tab sau có thể nhận 429 và cần chờ.
- Giới hạn theo bộ nhớ tiến trình, reset khi worker/instance khởi động lại; chỉ dành cho nhóm nhỏ dùng nội bộ. Không phải hệ thống SaaS đa người dùng hay bản đã kiểm toán bảo mật. Trước khi mở cho nhiều người cần tài khoản riêng, Redis/rate-limit dùng chung, monitoring, hàng đợi nền và kiểm toán bổ sung.
- Upload tối đa 12 MB. Không ghi key, file upload hoặc kết quả vào file/database. Nội dung được xử lý qua bộ nhớ server và gửi tới AddLiveTag khi gọi API.
- Render/GitHub là hạ tầng bên thứ ba; chính sách xử lý dữ liệu của họ áp dụng. Chỉ chủ sở hữu và người bạn tin tưởng nên biết mật khẩu tool.

## Free plan: dùng thử, không cam kết luôn sẵn sàng

Theo tài liệu Render, Free web service nghỉ sau 15 phút không có lưu lượng; lần mở lại có thể mất khoảng một phút để thức dậy. Free plan có giới hạn tài nguyên, giờ chạy/build/băng thông, có thể tạm dừng khi vượt hạn mức hoặc gọi ra ngoài quá nhiều. Render khuyên không dùng Free cho ứng dụng production.

- Nếu dùng thường xuyên và cần ổn định, tự xem xét gói compute trả phí trên Render hoặc VPS sau khi kiểm tra giá.
- Tắt máy tính của bạn không làm mất website đã triển khai, nhưng **tab phải còn mở trong lúc quét danh sách**: việc chia lô/đợi/chạy lô tiếp theo vẫn do trình duyệt điều khiển, chưa có hàng đợi nền chạy khi đóng tab.
- Tải lại/đóng tab sẽ mất kết quả chưa xuất. Hãy xuất Excel trước.
- Free service có thể khởi động lại; app này không dùng database lưu lịch sử riêng. Lịch sử được đọc từ API của AddLiveTag.

## Nếu gặp lỗi

| Thông báo | Kiểm tra |
|---|---|
| Không tìm thấy `render.yaml` | File phải ở gốc repo, không nằm trong ZIP hoặc thư mục con. |
| Thiếu Flask/Gunicorn | Build Command phải dùng `requirements-render.txt`. |
| `LINKSCOPE_PASSWORD ... 16 characters` | Render → service → Environment → đặt mật khẩu đủ dài, lưu và redeploy. |
| `SECRET_KEY ... 32 characters` | Triển khai bằng Blueprint để tự sinh secret, hoặc đặt chuỗi ngẫu nhiên dài trong Render Environment. Không đặt giá trị mẫu. |
| Đăng nhập rồi vẫn quay lại trang login | Mở URL **HTTPS** trực tiếp, cho phép cookie; không dùng iframe. |
| CSRF / phiên hết hạn | Tải lại trang và đăng nhập; kết quả chưa xuất có thể mất. Nên xuất trước khi bỏ tab lâu. |
| API 401 | Key AddLiveTag thiếu/không hợp lệ, không phải mật khẩu đăng nhập tool. |
| API 403 hoặc bị nhà cung cấp chặn | Kiểm tra quyền key/điều kiện nhà cung cấp; hỏi admin AddLiveTag về IP máy chủ Render. Không bảo đảm IP hosting được nguồn chấp nhận. |
| 429 | Tool hoặc nhà cung cấp đạt giới hạn; đợi rồi thử lại. |
| Trang mở chậm sau thời gian không dùng | Có thể Free service đang thức dậy; xem trạng thái service và log. |

Khi cần hỗ trợ, gửi URL website hoặc ảnh log **đã che mật khẩu/secret/key**. Không gửi toàn bộ trang Environment.

## Nguồn hướng dẫn hosting

- https://render.com/docs/deploy-flask
- https://render.com/docs/blueprint-spec
- https://render.com/docs/python-version
- https://render.com/docs/free

Tình trạng kiểm thử: đã kiểm thử local các chức năng tool, đăng nhập/đăng xuất, cookie, CSRF và rate limiting bằng dữ liệu giả lập. **Chưa triển khai lên tài khoản Render của bạn và chưa kiểm chứng số liệu thật với API Key của bạn.**
