import type { DetectedObject, GuidanceTip, SceneLabel } from "./types";

const GENERIC_TIPS: GuidanceTip[] = [
  {
    category: "Composition",
    text: "Try shooting from a different angle to add visual interest to your photo.",
  },
  {
    category: "Composition",
    text: "Look for a simple background that doesn't compete with your main subject.",
  },
  {
    category: "Composition",
    text: "Check the edges of your frame for distracting objects before you shoot.",
  },
  {
    category: "Composition",
    text: "Use the rule of thirds by placing key elements away from the center.",
  },
  {
    category: "Composition",
    text: "Include foreground elements to give your image a sense of depth.",
  },
  {
    category: "Lighting",
    text: "Use soft natural light when possible; it often flatters people and textures.",
  },
  {
    category: "Lighting",
    text: "Avoid harsh midday sun; seek open shade or shoot during the golden hour.",
  },
  {
    category: "Lighting",
    text: "Watch for unwanted shadows on faces; turn your subject toward the light source.",
  },
  {
    category: "Exposure",
    text: "Tap to expose for the most important part of the scene, then lock that exposure.",
  },
  {
    category: "Exposure",
    text: "If the sky is too bright, try exposing for the sky and letting shadows fall darker.",
  },
  {
    category: "Focus",
    text: "Make sure your main subject is the sharpest part of the image.",
  },
  {
    category: "Focus",
    text: "Use a shallow depth of field to separate your subject from a busy background.",
  },
  {
    category: "Color",
    text: "Look for complementary colors that make your subject stand out.",
  },
  {
    category: "Color",
    text: "Simplify your palette; too many competing colors can confuse the eye.",
  },
  {
    category: "Timing",
    text: "Wait for the decisive moment when expressions, poses, or action peak.",
  },
  {
    category: "Perspective",
    text: "Get closer to your subject; most photos benefit from removing unnecessary distance.",
  },
  {
    category: "Perspective",
    text: "Shoot from a low or high viewpoint to change how the viewer sees the scene.",
  },
  {
    category: "Framing",
    text: "Use doorways, windows, or branches to create a natural frame around your subject.",
  },
  {
    category: "Storytelling",
    text: "Include context in the frame so viewers understand where the photo was taken.",
  },
  {
    category: "Storytelling",
    text: "Capture small details as well as wide shots; they often tell the strongest story.",
  },
  {
    category: "Cropping",
    text: "Leave a little breathing room around your subject instead of cropping too tightly.",
  },
  {
    category: "Cropping",
    text: "Avoid cutting people at joints like wrists, knees, or ankles.",
  },
  {
    category: "Sharpness",
    text: "Hold the camera steady or lean against a surface to avoid camera shake.",
  },
  {
    category: "Details",
    text: "Clean the lens before shooting; smudges reduce contrast and sharpness.",
  },
];

const OUTDOOR_KEYWORDS = [
  "outdoor",
  "landscape",
  "mountain",
  "valley",
  "lake",
  "seashore",
  "beach",
  "coast",
  "ocean",
  "sky",
  "field",
  "meadow",
  "forest",
  "wood",
  "desert",
  "water",
  "waterfall",
  "canyon",
  "cliff",
  "sunset",
  "sunrise",
];

const INDOOR_KEYWORDS = [
  "indoor",
  "room",
  "kitchen",
  "living_room",
  "bedroom",
  "restaurant",
  "library",
  "office",
  "shop",
  "store",
  "classroom",
  "theater",
  "cinema",
];

function imageArea(width: number, height: number): number {
  return width * height;
}

function boxArea(box: DetectedObject["box"]): number {
  return (box.xmax - box.xmin) * (box.ymax - box.ymin);
}

function isCentered(box: DetectedObject["box"], width: number, height: number): boolean {
  const centerX = (box.xmin + box.xmax) / 2;
  const centerY = (box.ymin + box.ymax) / 2;
  const imageCenterX = width / 2;
  const imageCenterY = height / 2;
  const toleranceX = width * 0.15;
  const toleranceY = height * 0.15;
  return (
    Math.abs(centerX - imageCenterX) <= toleranceX &&
    Math.abs(centerY - imageCenterY) <= toleranceY
  );
}

function sceneLooksOutdoor(scenes: SceneLabel[]): boolean {
  return scenes.some((s) =>
    OUTDOOR_KEYWORDS.some((kw) => s.label.toLowerCase().includes(kw))
  );
}

function sceneLooksIndoor(scenes: SceneLabel[]): boolean {
  return scenes.some((s) =>
    INDOOR_KEYWORDS.some((kw) => s.label.toLowerCase().includes(kw))
  );
}

export function generateGuidance(
  detections: DetectedObject[],
  scenes: SceneLabel[],
  width: number,
  height: number,
  filename: string
) {
  const area = imageArea(width, height);
  const persons = detections.filter((d) => d.label === "person");
  const animals = detections.filter((d) =>
    ["dog", "cat", "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe", "bird"].includes(d.label)
  );
  const vehicles = detections.filter((d) =>
    ["bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck", "boat"].includes(d.label)
  );
  const foodOrDrink = detections.filter((d) =>
    ["bottle", "wine glass", "cup", "fork", "knife", "spoon", "bowl", "banana", "apple", "sandwich", "orange", "broccoli", "carrot", "hot dog", "pizza", "donut", "cake"].includes(d.label)
  );

  const tips: GuidanceTip[] = [];

  // Person rules
  if (persons.length === 1) {
    const person = persons[0];
    if (isCentered(person.box, width, height)) {
      tips.push({
        category: "Composition",
        text: "The subject is centered. Try placing them off-center using the rule of thirds for a more dynamic photo.",
        reason: "Centered subjects can feel static.",
      });
    }
    const personAreaRatio = boxArea(person.box) / area;
    if (personAreaRatio < 0.08) {
      tips.push({
        category: "Subject",
        text: "The person looks small in the frame. Move closer or zoom in so they become the clear focal point.",
        reason: "The person occupies less than 8% of the image area.",
      });
    } else if (personAreaRatio > 0.6) {
      tips.push({
        category: "Composition",
        text: "The person fills most of the frame. Try stepping back slightly to include a bit more context.",
        reason: "Very tight framing can feel cramped.",
      });
    }
  } else if (persons.length > 1) {
    tips.push({
      category: "Composition",
      text: "With multiple people, watch the spacing between them and avoid cropping at joints like wrists or ankles.",
      reason: `Detected ${persons.length} people.`,
    });
  }

  // Animal rules
  if (animals.length > 0 && persons.length === 0) {
    tips.push({
      category: "Subject",
      text: "Get down to the animal's eye level for a more engaging and intimate portrait.",
      reason: `Detected ${animals[0].label}.`,
    });
  }

  // Vehicle / transport rules
  if (vehicles.length > 0) {
    tips.push({
      category: "Composition",
      text: "Keep the horizon straight and look for leading lines that guide the eye toward the vehicle.",
      reason: `Detected ${vehicles[0].label}.`,
    });
  }

  // Food / product rules
  if (foodOrDrink.length > 0 && persons.length === 0 && animals.length === 0) {
    tips.push({
      category: "Lighting",
      text: "Soft, diffused light from the side helps show texture and makes food or products look appealing.",
      reason: `Detected ${foodOrDrink[0].label}.`,
    });
  }

  // Scene-based lighting tips
  if (sceneLooksOutdoor(scenes)) {
    tips.push({
      category: "Lighting",
      text: "Outdoor scenes often look best during the golden hour, shortly after sunrise or before sunset.",
      reason: "Scene appears to be outdoors.",
    });
  } else if (sceneLooksIndoor(scenes)) {
    tips.push({
      category: "Lighting",
      text: "Indoors, place your subject near a large window for soft, natural light.",
      reason: "Scene appears to be indoors.",
    });
  }

  // Aspect ratio tip
  const ratio = width / height;
  if (ratio > 1.6) {
    tips.push({
      category: "Composition",
      text: "Your photo is very wide. Use horizontal lines or sweeping foreground elements to emphasize the panorama.",
      reason: "Image aspect ratio is strongly landscape.",
    });
  } else if (ratio < 0.625) {
    tips.push({
      category: "Composition",
      text: "Your photo is very tall. Vertical leading lines or height in the subject can emphasize the format.",
      reason: "Image aspect ratio is strongly portrait.",
    });
  }

  // Ensure at least one tip
  if (tips.length === 0) {
    const genericIndex = filename.length % GENERIC_TIPS.length;
    tips.push(GENERIC_TIPS[genericIndex]);
  }

  // Limit to top 3 tips
  const finalTips = tips.slice(0, 3);

  // Build summary
  const labels = detections.map((d) => d.label);
  const uniqueLabels = [...new Set(labels)].slice(0, 3);
  const sceneNames = scenes.slice(0, 2).map((s) => s.label.replace(/_/g, " "));
  let summary: string;
  if (uniqueLabels.length > 0 && sceneNames.length > 0) {
    summary = `A photo featuring ${uniqueLabels.join(", ")} in a ${sceneNames.join(", ")} setting.`;
  } else if (uniqueLabels.length > 0) {
    summary = `A photo featuring ${uniqueLabels.join(", ")}.`;
  } else if (sceneNames.length > 0) {
    summary = `A photo of a ${sceneNames.join(", ")} scene.`;
  } else {
    summary = "A photo with no strong detected subjects.";
  }

  const uncertain = detections.length === 0 || detections.every((d) => d.score < 0.6);

  return {
    summary,
    subjects: detections,
    scenes: scenes.slice(0, 3),
    tips: finalTips,
    uncertain,
    notice: uncertain
      ? "Suggestions are general because the scene or subjects could not be identified confidently."
      : null,
    error_message: null,
  };
}
