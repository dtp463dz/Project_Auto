import numpy as np
import cv2

def make_feather_mask(w, h, feather_px):
    """Tạo mask alpha (0-255) kích thước (h, w): 255 ở giữa, mờ dần về 0 ở biên
    trong khoảng feather_px pixel. feather_px = 0 -> mask đặc toàn bộ (dán thô)."""
    mask = np.full((h, w), 255, dtype=np.float32)
    feather_px = max(0, int(feather_px))
    if feather_px <= 0:
        return mask

    # không cho feather lớn hơn nửa cạnh ngắn nhất, tránh mask bị rỗng toàn bộ
    feather_px = min(feather_px, max(1, min(w, h) // 2 - 1))

    mask[:feather_px, :] = 0
    mask[h - feather_px:, :] = 0
    mask[:, :feather_px] = 0
    mask[:, w - feather_px:] = 0

    sigma = max(1.0, feather_px / 2.0)
    mask = cv2.GaussianBlur(mask, (0, 0), sigmaX=sigma, sigmaY=sigma)
    return mask

def cut_patch(source_bgr, rect):
    """Cắt vùng ảnh theo rect = (x, y, w, h) (int, toạ độ pixel ảnh nguồn).
    Trả về mảng numpy BGR đã cắt (copy, không ảnh hưởng ảnh gốc)."""
    x, y, w, h = rect
    sh, sw = source_bgr.shape[:2]
    x = max(0, min(x, sw - 1))
    y = max(0, min(y, sh - 1))
    w = max(1, min(w, sw - x))
    h = max(1, min(h, sh - y))
    return source_bgr[y:y + h, x:x + w].copy(), (x, y, w, h)


def composite_paste(target_bgr, patch_bgr, paste_x, paste_y, feather_px=12):
    """Dán patch_bgr vào target_bgr tại toạ độ (paste_x, paste_y) (góc trên-trái),
    blend biên theo feather_px. Tự clip nếu vùng dán vượt ra ngoài ảnh đích.
    Trả về ảnh đích đã ghép (KHÔNG sửa target_bgr gốc, trả về bản copy) và
    rect thực tế đã dán (sau khi clip) dạng (x, y, w, h) - dùng để tính bbox nhãn.
    """
    result = target_bgr.copy()
    th, tw = result.shape[:2]
    ph, pw = patch_bgr.shape[:2]

    # vùng đích cần dán (trước khi clip)
    dst_x0, dst_y0 = paste_x, paste_y
    dst_x1, dst_y1 = paste_x + pw, paste_y + ph

    # phần patch tương ứng còn nằm trong ảnh đích sau khi clip
    src_x0 = max(0, -dst_x0)
    src_y0 = max(0, -dst_y0)
    dst_x0c = max(0, dst_x0)
    dst_y0c = max(0, dst_y0)
    dst_x1c = min(tw, dst_x1)
    dst_y1c = min(th, dst_y1)

    if dst_x1c <= dst_x0c or dst_y1c <= dst_y0c:
        # dán hoàn toàn ra ngoài ảnh đích - không làm gì cả
        return result, (dst_x0c, dst_y0c, 0, 0)

    w = dst_x1c - dst_x0c
    h = dst_y1c - dst_y0c
    patch_crop = patch_bgr[src_y0:src_y0 + h, src_x0:src_x0 + w]

    mask = make_feather_mask(pw, ph, feather_px)
    mask_crop = mask[src_y0:src_y0 + h, src_x0:src_x0 + w]
    alpha = (mask_crop / 255.0)[:, :, None]

    region = result[dst_y0c:dst_y1c, dst_x0c:dst_x1c].astype(np.float32)
    blended = patch_crop.astype(np.float32) * alpha + region * (1 - alpha)
    result[dst_y0c:dst_y1c, dst_x0c:dst_x1c] = np.clip(blended, 0, 255).astype(np.uint8)

    return result, (dst_x0c, dst_y0c, w, h)
